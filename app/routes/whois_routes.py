# app/routes/whois_routes.py
from flask import Blueprint, jsonify, current_app
import whois
from whois.parser import PywhoisError
from datetime import datetime

def _serialize(value):
    """Recursively convert WHOIS objects into JSON serialisable types."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int, float, bool, type(None), str)):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except Exception:
            return value.decode('latin-1', 'ignore')
    if isinstance(value, (list, tuple, set)):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return str(value)

whois_bp = Blueprint('whois', __name__, url_prefix='/api/whois')

@whois_bp.route('/<domain_name>')
def get_whois_info(domain_name):
    """도메인 Whois 정보를 조회하여 JSON으로 반환합니다."""
    try:
        # 여기에서 도메인 이름 유효성 검사를 추가할 수 있습니다.
        w = whois.whois(domain_name)

        result = {k: _serialize(v) for k, v in w.__dict__.items() if not k.startswith('_')}
        return jsonify(result)
    except PywhoisError:
        return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
    except Exception as e:
        current_app.logger.error(f"Whois 조회 오류: {e}")
        return jsonify({'error': 'Whois 정보를 조회하는 중 오류가 발생했습니다.'}), 500