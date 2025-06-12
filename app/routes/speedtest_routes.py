# app/routes/speedtest_routes.py
from flask import Blueprint, render_template, current_app, jsonify, request, Response
from app import csrf # app/__init__.py 에서 생성된 csrf 객체를 가져옵니다.

# 블루프린트 생성
speedtest_bp = Blueprint('speedtest', __name__, url_prefix='/speedtest')

@speedtest_bp.route('/')
def speedtest_page():
    """네트워크 속도 테스트 페이지를 렌더링합니다."""
    try:
        return render_template('speedtest.html')
    except Exception as e:
        current_app.logger.error(f'Speedtest 페이지 로드 에러: {e}')
        return render_template('500.html', error_message="Speedtest 페이지를 로드할 수 없습니다."), 500

@speedtest_bp.route('/ip')
def get_ip():
    """클라이언트의 IP 주소를 반환합니다."""
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return jsonify(ip=ip)

@speedtest_bp.route('/ping_target')
def ping_target():
    """핑 테스트 대상 엔드포인트입니다."""
    return jsonify(status="ok")

@speedtest_bp.route('/download')
def download_test_file():
    """다운로드 속도 테스트용 파일을 제공합니다."""
    size_mb_str_from_request = request.args.get('size_mb', '10')
    try:
        size_mb_float = float(size_mb_str_from_request)
        # 아래 줄의 100을 150으로 수정했습니다.
        if not (0.1 <= size_mb_float <= 150):
            current_app.logger.warning(f"다운로드 테스트: 요청된 파일 크기 범위를 벗어남 ({size_mb_float}MB)")
            # 아래 에러 메시지의 100MB를 150MB로 수정했습니다.
            raise ValueError("크기 범위를 벗어났습니다 (0.1MB ~ 150MB).")

        total_bytes_to_send = int(size_mb_float * 1024 * 1024)
        one_mb_chunk = b'0' * (1024 * 1024)

        def generate_data():
            bytes_sent = 0
            while bytes_sent < total_bytes_to_send:
                current_chunk_size = min(len(one_mb_chunk), total_bytes_to_send - bytes_sent)
                if current_chunk_size == len(one_mb_chunk):
                    yield one_mb_chunk
                else:
                    yield one_mb_chunk[:current_chunk_size]
                bytes_sent += current_chunk_size
        
        response_headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename=download_test_{size_mb_float}mb.dat',
            'Content-Length': str(total_bytes_to_send)
        }
        return Response(generate_data(), headers=response_headers)

    except ValueError as e:
        current_app.logger.error(f"다운로드 테스트 오류: 잘못된 size_mb 값 '{size_mb_str_from_request}'. 오류: {e}")
        return Response("잘못된 크기 매개변수입니다.", status=400, mimetype='text/plain')
    except Exception as e:
        current_app.logger.error(f"다운로드 테스트 중 예기치 않은 오류 발생 (size_mb_str='{size_mb_str_from_request}'): {e}", exc_info=True)
        return Response("다운로드 파일 생성 중 오류가 발생했습니다.", status=500, mimetype='text/plain')

@speedtest_bp.route('/upload', methods=['POST'])
@csrf.exempt # CSRF 보호에서 이 라우트를 제외합니다.
def upload_test_file():
    """업로드 속도 테스트용 데이터를 받습니다."""
    try:
        uploaded_data_length = len(request.get_data(as_text=False))
        current_app.logger.debug(f"업로드 테스트: {uploaded_data_length} bytes 수신")
        return jsonify(status="ok", message="업로드 성공")
    except Exception as e:
        current_app.logger.error(f"업로드 테스트 오류: {e}", exc_info=True)
        return jsonify(status="error", message="업로드 처리 중 오류 발생"), 500