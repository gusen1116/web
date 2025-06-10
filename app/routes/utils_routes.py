from flask import Blueprint, render_template, request, Response, stream_with_context, jsonify
import socket
import ipaddress
import concurrent.futures
import json

# 유틸리티 기능을 위한 블루프린트 생성
utils_bp = Blueprint('utils_bp', __name__)

def is_valid_host(host):
    """제공된 문자열이 유효한 호스트 이름 또는 IP 주소인지 확인합니다."""
    try:
        # gethostbyname은 호스트 이름을 IP 주소로 변환합니다.
        # 변환이 성공하면 유효한 호스트로 간주합니다.
        socket.gethostbyname(host)
        return True
    except (socket.gaierror, ValueError):
        return False

def scan_port(host, port):
    """
    단일 포트를 스캔하고 상태를 반환합니다.
    (열림, 닫힘, 또는 에러)
    """
    try:
        # 소켓 생성 (IPv4, TCP)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 연결 시도에 대한 타임아웃을 1초로 설정
        sock.settimeout(1)
        # connect_ex는 연결 성공 시 0, 실패 시 에러 코드를 반환합니다.
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return {'port': port, 'status': 'Open', 'error': False}
        else:
            return {'port': port, 'status': 'Closed', 'error': False}
    except Exception as e:
        # 스캔 중 다른 예외 발생 시 에러 정보 반환
        return {'port': port, 'status': str(e), 'error': True}

@utils_bp.route('/portscanner', methods=['GET'])
def port_scanner_page():
    """포트 스캐너 페이지를 렌더링합니다."""
    return render_template('port_scanner.html')

@utils_bp.route('/start_portscan', methods=['POST'])
def start_portscan():
    """포트 스캔을 시작하고 결과를 스트리밍합니다."""
    host = request.form.get('host')
    try:
        start_port = int(request.form.get('start_port'))
        end_port = int(request.form.get('end_port'))
    except (ValueError, TypeError):
        # 포트 번호가 유효하지 않을 경우
        return Response(json.dumps({'error': '유효하지 않은 포트 번호입니다.'}), status=400, mimetype='application/json')

    # 호스트 이름 유효성 검사
    if not host or not is_valid_host(host):
        return Response(json.dumps({'error': '유효하지 않거나 비어있는 호스트 이름/IP 주소입니다.'}), status=400, mimetype='application/json')

    # 스캔 전 호스트 이름을 IP로 한 번만 변환
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return Response(json.dumps({'error': f"호스트 이름 '{host}'을(를) 확인할 수 없습니다."}), status=400, mimetype='application/json')

    # 포트 범위 유효성 검사
    if not (0 < start_port <= 65535 and 0 < end_port <= 65535 and start_port <= end_port):
         return Response(json.dumps({'error': '포트 범위는 1과 65535 사이여야 하며, 시작 포트는 종료 포트보다 작거나 같아야 합니다.'}), status=400, mimetype='application/json')

    def generate_results():
        """포트를 스캔하고 결과를 생성(yield)하는 제너레이터 함수입니다."""
        ports_to_scan = range(start_port, end_port + 1)
        # ThreadPoolExecutor를 사용하여 I/O 바운드 작업을 동시에 처리
        # max_workers는 동시에 실행할 최대 스레드 수를 의미
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            # 각 포트 스캔 작업을 스레드 풀에 제출
            future_to_port = {executor.submit(scan_port, target_ip, port): port for port in ports_to_scan}

            # as_completed는 작업이 완료되는 순서대로 future를 반환
            for future in concurrent.futures.as_completed(future_to_port):
                try:
                    data = future.result()
                    # Server-Sent Events (SSE) 형식으로 데이터를 클라이언트에 yield
                    yield f"data: {json.dumps(data)}\n\n"
                except Exception as e:
                    port = future_to_port[future]
                    error_data = {'port': port, 'status': f'Error: {e}', 'error': True}
                    yield f"data: {json.dumps(error_data)}\n\n"
        # 모든 스캔이 완료되었음을 알리는 메시지 전송
        yield f"data: {json.dumps({'status': 'finished'})}\n\n"

    # 스트리밍 응답을 반환
    return Response(stream_with_context(generate_results()), mimetype='text/event-stream')
