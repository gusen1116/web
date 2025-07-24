# app/routes/whois_routes.py
from flask import Blueprint, jsonify, current_app
import whois
from whois.parser import PywhoisError
from datetime import datetime

def _serialize(value):
    """
    WHOIS 객체를 JSON으로 직렬화할 수 있는 타입으로 재귀적으로 변환합니다.
    - 리스트 내의 모든 항목을 직렬화합니다.
    - datetime 객체를 ISO 형식 문자열로 변환합니다.
    - bytes를 utf-8로 디코딩합니다.
    - 나머지 타입은 문자열로 변환합니다.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        # 리스트의 각 항목을 재귀적으로 직렬화하고 None이 아닌 값만 필터링합니다.
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
    # 다른 모든 타입은 문자열로 변환합니다.
    return str(value)

whois_bp = Blueprint('whois', __name__, url_prefix='/api/whois')

@whois_bp.route('/<domain_name>')
def get_whois_info(domain_name):
    """도메인 Whois 정보를 조회하여 JSON으로 반환합니다."""
    try:
        # 도메인 이름 유효성 검사 (간단한 예시)
        if not domain_name or '.' not in domain_name:
            return jsonify({'error': '유효하지 않은 도메인 이름입니다.'}), 400

        w = whois.whois(domain_name)

        # whois 결과가 비어있는 경우 (예: text 속성이 없는 경우)
        if not hasattr(w, 'text') or not w.text:
            # PywhoisError를 발생시키지 않고 결과가 없는 경우 처리
            if not any(w.values()):
                return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
        
        # 직렬화가 필요한 키만 선별하여 처리
        result = {k: _serialize(v) for k, v in w.items() if not k.startswith('_')}
        
        # 필수 정보가 하나도 없는 경우 에러 처리
        required_keys = ['domain_name', 'registrar', 'creation_date', 'expiration_date']
        if not any(key in result and result[key] for key in required_keys):
            # 결과는 있으나 유의미한 정보가 없는 경우
            if not w.text:
                return jsonify({'error': f"'{domain_name}' 도메인에 대한 유의미한 정보를 찾을 수 없습니다."}), 404

        return jsonify(result)
        
    except PywhoisError as e:
        # 라이브러리가 명시적으로 에러를 발생시키는 경우
        current_app.logger.warning(f"Whois 조회 실패 (PywhoisError): {domain_name} - {e}")
        return jsonify({'error': f"'{domain_name}' 도메인 정보를 찾을 수 없습니다."}), 404
        
    except Exception as e:
        # 그 외 모든 예외 처리
        current_app.logger.error(f"Whois 조회 중 알 수 없는 오류: {domain_name} - {e}", exc_info=True)
        return jsonify({'error': 'Whois 정보를 조회하는 중 서버 오류가 발생했습니다.'}), 500