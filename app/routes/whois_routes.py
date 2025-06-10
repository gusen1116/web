# app/routes/whois_routes.py
from flask import Blueprint, jsonify, current_app
import whois
from whois.parser import PywhoisError

whois_bp = Blueprint('whois', __name__, url_prefix='/api/whois')

@whois_bp.route('/<domain_name>')
def get_whois_info(domain_name):
    """도메인 Whois 정보를 조회하여 JSON으로 반환합니다."""
    try:
        # 여기에서 도메인 이름 유효성 검사를 추가할 수 있습니다.
        w = whois.whois(domain_name)

        # whois 라이브러리가 날짜를 리스트로 반환하는 경우가 있어 처리
        creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
        expiration_date = w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date

        # 필요한 정보만 가공하여 반환
        result = {
            'domain_name': w.domain_name,
            'registrar': w.registrar,
            'creation_date': creation_date.isoformat() if creation_date else None,
            'expiration_date': expiration_date.isoformat() if expiration_date else None,
            'name_servers': w.name_servers,
            'status': w.status,
            'emails': w.emails,
            'updated_date': w.updated_date[0].isoformat() if isinstance(w.updated_date, list) else w.updated_date.isoformat() if w.updated_date else None,
        }
        return jsonify(result)
    except PywhoisError:
        return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
    except Exception as e:
        current_app.logger.error(f"Whois 조회 오류: {e}")
        return jsonify({'error': 'Whois 정보를 조회하는 중 오류가 발생했습니다.'}), 500