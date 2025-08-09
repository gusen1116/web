"""
app/routes/whois_routes.py
-------------------------

Routes that provide WHOIS lookup functionality. The endpoint now declares
the domain name as part of the URL instead of relying on a trailing space,
which ensures proper parameter capture.
"""

from flask import Blueprint, jsonify, current_app
import whois
from whois.parser import PywhoisError
from datetime import datetime

def _serialize(value):
    """Recursively serialize WHOIS values into JSON-friendly types."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [item for item in (_serialize(v) for v in value) if item]
    if isinstance(value, (int, float, bool, type(None))):
        return value
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8').strip()
        except UnicodeDecodeError:
            return value.decode('latin-1', 'ignore').strip()
    return str(value)

whois_bp = Blueprint('whois', __name__, url_prefix='/api/whois')

@whois_bp.route('/<domain_name>')
def get_whois_info(domain_name: str):
    """Look up WHOIS information for ``domain_name`` and return it as JSON."""
    try:
        if not domain_name or '.' not in domain_name:
            return jsonify({'error': '유효하지 않은 도메인 이름입니다.'}), 400
        w = whois.whois(domain_name)
        if not hasattr(w, 'text') or not w.text:
            if not any(w.values()):
                return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
        result = {k: _serialize(v) for k, v in w.items() if not k.startswith('_')}
        required_keys = ['domain_name', 'registrar', 'creation_date', 'expiration_date']
        if not any(key in result and result[key] for key in required_keys):
            if not w.text:
                return jsonify({'error': f"'{domain_name}' 도메인에 대한 유의미한 정보를 찾을 수 없습니다."}), 404
        return jsonify(result)
    except PywhoisError as e:
        current_app.logger.warning(f"Whois 조회 실패 (PywhoisError): {domain_name} - {e}")
        return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
    except Exception as e:
        current_app.logger.error(f"Whois 조회 중 알 수 없는 오류: {domain_name} - {e}", exc_info=True)
        return jsonify({'error': 'Whois 정보를 조회하는 중 서버 오류가 발생했습니다.'}), 500