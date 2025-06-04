# app/routes/speedtest_routes.py
import os
import time
from flask import Blueprint, render_template, request, jsonify, Response

# 'speedtest' 라는 이름으로 블루프린트 생성, URL 접두사는 /speedtest 로 설정
speedtest_bp = Blueprint('speedtest', __name__, url_prefix='/speedtest')

DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB

@speedtest_bp.route('/')
def speedtest_page():
    """네트워크 속도 테스트 페이지를 렌더링합니다."""
    return render_template('speedtest.html') # 새로운 HTML 템플릿을 사용

@speedtest_bp.route('/ping_target')
def ping_target():
    """핑 테스트를 위한 엔드포인트입니다."""
    return jsonify(status="ok")

@speedtest_bp.route('/ip')
def get_ip():
    """클라이언트의 IP 주소를 반환합니다."""
    if request.headers.getlist("X-Forwarded-For"):
       ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
       ip = request.remote_addr
    return jsonify(ip=ip)

@speedtest_bp.route('/download')
def download_file():
    """다운로드 속도 테스트를 위한 파일을 스트리밍합니다."""
    size_mb_str = request.args.get('size_mb', '10') # 기본 10MB
    try:
        size_mb = int(size_mb_str)
        if not 1 <= size_mb <= 200: # 1MB ~ 200MB 제한
            raise ValueError("Size out of range")
    except ValueError:
        return "Invalid size_mb parameter. Must be an integer between 1 and 200.", 400

    total_size_bytes = size_mb * 1024 * 1024

    def generate_data():
        bytes_sent = 0
        # 지정된 크기만큼 랜덤 바이트 데이터 생성하여 청크 단위로 전송
        while bytes_sent < total_size_bytes:
            chunk = os.urandom(min(DOWNLOAD_CHUNK_SIZE, total_size_bytes - bytes_sent))
            yield chunk
            bytes_sent += len(chunk)

    # HTTP 응답으로 데이터 스트리밍
    return Response(generate_data(), mimetype='application/octet-stream', headers={
        'Content-Disposition': f'attachment; filename=dummy_file_{size_mb}mb.dat',
        'Content-Length': str(total_size_bytes)
    })

@speedtest_bp.route('/upload', methods=['POST'])
def upload_file():
    """업로드 속도 테스트를 위한 엔드포인트입니다. 받은 데이터는 사용하지 않습니다."""
    # 클라이언트로부터 받은 데이터의 길이를 JSON으로 응답
    return jsonify(status="ok", received_bytes=request.content_length)