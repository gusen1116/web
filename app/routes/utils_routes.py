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

    # 포트 범위 유효성 검사 (최대 2000개로 증가)
    if not (0 < start_port <= 65535 and 0 < end_port <= 65535 and start_port <= end_port):
        return Response(json.dumps({'error': '포트 범위는 1과 65535 사이여야 하며, 시작 포트는 종료 포트보다 작거나 같아야 합니다.'}), status=400, mimetype='application/json')
    
    # 최대 2000개 포트로 제한
    if end_port - start_port + 1 > 2000:
        return Response(json.dumps({'error': '한 번에 스캔할 수 있는 최대 포트 수는 2000개입니다.'}), status=400, mimetype='application/json')

    def generate_results():
        """포트를 스캔하고 결과를 생성(yield)하는 제너레이터 함수입니다."""
        ports_to_scan = range(start_port, end_port + 1)
        total_ports = len(ports_to_scan)
        
        # 스캔 시작 메시지
        yield f"data: {json.dumps({'status': 'start', 'total': total_ports, 'host': host, 'ip': target_ip})}\n\n"
        
        # ThreadPoolExecutor를 사용하여 I/O 바운드 작업을 동시에 처리
        # max_workers는 동시에 실행할 최대 스레드 수를 의미 (증가)
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
            # 각 포트 스캔 작업을 스레드 풀에 제출
            future_to_port = {executor.submit(scan_port, target_ip, port): port for port in ports_to_scan}
            
            scanned_count = 0
            
            # as_completed는 작업이 완료되는 순서대로 future를 반환
            for future in concurrent.futures.as_completed(future_to_port):
                try:
                    data = future.result()
                    scanned_count += 1
                    
                    # 진행률 정보와 함께 결과 전송
                    data['progress'] = {
                        'current': scanned_count,
                        'total': total_ports,
                        'percentage': round((scanned_count / total_ports) * 100, 1)
                    }
                    
                    # Server-Sent Events (SSE) 형식으로 데이터를 클라이언트에 yield
                    yield f"data: {json.dumps(data)}\n\n"
                    
                except Exception as e:
                    port = future_to_port[future]
                    scanned_count += 1
                    error_data = {
                        'port': port, 
                        'status': f'Error: {e}', 
                        'error': True,
                        'progress': {
                            'current': scanned_count,
                            'total': total_ports,
                            'percentage': round((scanned_count / total_ports) * 100, 1)
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
        
        # 모든 스캔이 완료되었음을 알리는 메시지 전송
        yield f"data: {json.dumps({'status': 'finished', 'total_scanned': scanned_count})}\n\n"

    # 스트리밍 응답을 반환
    return Response(stream_with_context(generate_results()), mimetype='text/event-stream')

# API 엔드포인트 추가 (프론트엔드에서 쉽게 사용할 수 있도록)
@utils_bp.route('/api/utils/port_scan', methods=['GET'])
def api_port_scan():
    """API 형태의 포트 스캔 엔드포인트"""
    host = request.args.get('host')
    ports_str = request.args.get('ports', '')
    
    if not host:
        return jsonify({'error': '호스트를 지정해주세요.'}), 400
    
    if not is_valid_host(host):
        return jsonify({'error': '유효하지 않은 호스트입니다.'}), 400
    
    # 포트 파싱
    ports_to_scan = []
    try:
        # 쉼표로 분리된 포트들 처리
        for port_part in ports_str.split(','):
            port_part = port_part.strip()
            if '-' in port_part:
                # 범위 처리 (예: 80-85)
                start, end = port_part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                if start > end:
                    start, end = end, start
                # 범위가 너무 크면 제한
                if end - start > 2000:
                    return jsonify({'error': '포트 범위가 너무 큽니다. 최대 2000개까지 가능합니다.'}), 400
                ports_to_scan.extend(range(start, end + 1))
            else:
                # 단일 포트
                ports_to_scan.append(int(port_part))
    except ValueError:
        return jsonify({'error': '잘못된 포트 형식입니다.'}), 400
    
    # 중복 제거 및 정렬
    ports_to_scan = sorted(list(set(ports_to_scan)))
    
    # 최대 포트 수 제한
    if len(ports_to_scan) > 2000:
        return jsonify({'error': '한 번에 스캔할 수 있는 최대 포트 수는 2000개입니다.'}), 400
    
    if not ports_to_scan:
        return jsonify({'error': '스캔할 포트를 지정해주세요.'}), 400
    
    # 간단한 동기 스캔 (API용)
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({'error': f"호스트 '{host}'를 확인할 수 없습니다."}), 400
    
    results = {
        'host': host,
        'ip': target_ip,
        'open': [],
        'closed': [],
        'errors': []
    }
    
    # 빠른 스캔을 위해 타임아웃을 짧게 설정
    for port in ports_to_scan[:100]:  # API는 최대 100개로 제한
        result = scan_port(target_ip, port)
        if result['error']:
            results['errors'].append(port)
        elif result['status'] == 'Open':
            results['open'].append(port)
        else:
            results['closed'].append(port)
    
    return jsonify(results)