# app/routes/speedtest_routes.py
from flask import Blueprint, render_template, current_app, jsonify, request, Response

# 블루프린트 생성
speedtest_bp = Blueprint('speedtest', __name__, url_prefix='/speedtest')

@speedtest_bp.route('/')
def speedtest_page():
    """네트워크 속도 테스트 페이지를 렌더링합니다."""
    try:
        return render_template('speedtest.html')
    except Exception as e:
        current_app.logger.error(f'Speedtest 페이지 로드 에러: {e}')
        # 필요한 경우 특정 에러 페이지를 렌더링하거나 대체 처리합니다.
        return render_template('500.html', error_message="Speedtest 페이지를 로드할 수 없습니다."), 500

@speedtest_bp.route('/ip')
def get_ip():
    """클라이언트의 IP 주소를 반환합니다."""
    # 프록시 서버를 사용하는 경우 X-Forwarded-For 헤더 확인
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return jsonify(ip=ip)

@speedtest_bp.route('/ping_target')
def ping_target():
    """핑 테스트 대상 엔드포인트입니다. 도달 가능성 및 지연 시간 확인용입니다."""
    # 실제 특별한 로직 없이 정상 응답만으로 충분합니다.
    return jsonify(status="ok")

@speedtest_bp.route('/download')
def download_test_file():
    """다운로드 속도 테스트용 파일을 제공합니다."""
    try:
        size_mb_str = request.args.get('size_mb', '10')  # 기본 10MB
        size_mb = int(size_mb_str)
        
        # 안전을 위해 파일 크기 제한 (1MB ~ 100MB 사이)
        if not (1 <= size_mb <= 100): 
            current_app.logger.warning(f"다운로드 테스트: 요청된 파일 크기 범위를 벗어남 ({size_mb}MB)")
            raise ValueError("크기 범위를 벗어났습니다.")
        
        # 1MB 크기의 '0'으로 채워진 청크 데이터 생성
        data_chunk = b'0' * (1024 * 1024) 
        
        def generate_data():
            for _ in range(size_mb):
                yield data_chunk
        
        # 응답 헤더 설정
        response_headers = {
            'Content-Type': 'application/octet-stream',  # 명확한 MIME 타입 지정
            'Content-Disposition': f'attachment; filename=download_test_{size_mb}mb.dat',
            'Content-Length': str(size_mb * 1024 * 1024)
        }
        
        return Response(generate_data(), headers=response_headers)
    
    except ValueError as e:
        current_app.logger.error(f"다운로드 테스트 오류: 잘못된 size_mb 값 - {e}")
        return Response("잘못된 크기 매개변수입니다.", status=400, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"다운로드 테스트 오류: {e}", exc_info=True)
        return Response("다운로드 파일 생성 중 오류가 발생했습니다.", status=500, mimetype='text/plain')

@speedtest_bp.route('/upload', methods=['POST'])
def upload_test_file():
    """업로드 속도 테스트용 데이터를 받습니다."""
    try:
        # 데이터 수신 (실제 저장할 필요는 없음)
        # request.data 또는 request.stream을 통해 데이터를 받을 수 있습니다.
        # 여기서는 데이터 크기만 확인하거나, 간단히 데이터를 읽는 것만으로도
        # 클라이언트 측에서 업로드 속도 측정이 가능합니다.
        # 예를 들어, 데이터 크기를 로깅할 수 있습니다.
        uploaded_data_length = len(request.get_data(as_text=False))
        current_app.logger.debug(f"업로드 테스트: {uploaded_data_length} bytes 수신")
        
        return jsonify(status="ok", message="업로드 성공")
    except Exception as e:
        current_app.logger.error(f"업로드 테스트 오류: {e}", exc_info=True)
        return jsonify(status="error", message="업로드 처리 중 오류 발생"), 500