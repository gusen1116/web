# app/routes/utils_routes.py (CSRF 헤더 검증 추가)
from flask import Blueprint, render_template, request, Response, stream_with_context, jsonify, current_app
import socket
import concurrent.futures
import json
from flask_wtf.csrf import verify_csrf

# 유틸리티 기능을 위한 블루프린트 생성
utils_bp = Blueprint('utils_bp', __name__)

def is_valid_host(host):
    """제공된 문자열이 유효한 호스트 이름 또는 IP 주소인지 확인합니다."""
    try:
        socket.gethostbyname(host)
        return True
    except (socket.gaierror, ValueError):
        return False

def scan_port(host, port):
    """단일 포트를 스캔하고 상태를 반환합니다."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return {'port': port, 'status': 'Open', 'error': False}
        else:
            return {'port': port, 'status': 'Closed', 'error': False}
    except Exception as e:
        return {'port': port, 'status': str(e), 'error': True}

@utils_bp.route('/portscanner', methods=['GET'])
def port_scanner_page():
    """포트 스캐너 페이지를 렌더링합니다."""
    return render_template('port_scanner.html')

@utils_bp.route('/start_portscan', methods=['POST'])
def start_portscan():
    """포트 스캔을 시작하고 결과를 스트리밍합니다. - CSRF 헤더 검증"""
    try:
        # CSRF 토큰 검증 (헤더 우선)
        csrf_token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        if csrf_token:
            verify_csrf(csrf_token)
        elif request.form.get('csrf_token'):
            from flask_wtf.csrf import validate_csrf
            validate_csrf(request.form.get('csrf_token'))
        # JSON 요청의 경우 헤더에서만 CSRF 검증
        elif request.is_json:
            if not csrf_token:
                return Response(json.dumps({'error': 'CSRF 토큰이 필요합니다'}), 
                              status=403, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'error': 'CSRF 검증 실패'}), 
                      status=403, mimetype='application/json')
    
    # Content-Type 확인하여 적절한 방식으로 데이터 추출
    if request.is_json:
        data = request.get_json()
        host = data.get('host')
        ports_to_scan = data.get('ports', [])
        
        if isinstance(ports_to_scan, str):
            try:
                ports_to_scan = json.loads(ports_to_scan)
            except json.JSONDecodeError:
                return Response(json.dumps({'error': '유효하지 않은 포트 형식입니다.'}), 
                              status=400, mimetype='application/json')
    else:
        host = request.form.get('host')
        ports_json_str = request.form.get('ports')
        
        try:
            if not ports_json_str:
                return Response(json.dumps({'error': '포트 목록이 비어있습니다.'}), 
                              status=400, mimetype='application/json')
            
            ports_to_scan = json.loads(ports_json_str)
        except (json.JSONDecodeError, ValueError) as e:
            return Response(json.dumps({'error': f'유효하지 않은 포트 형식입니다: {e}'}), 
                          status=400, mimetype='application/json')

    # 호스트 이름 유효성 검사
    if not host or not is_valid_host(host):
        return Response(json.dumps({'error': '유효하지 않거나 비어있는 호스트 이름/IP 주소입니다.'}), 
                      status=400, mimetype='application/json')

    # 포트 목록 유효성 검사
    if not isinstance(ports_to_scan, list) or not all(isinstance(p, int) for p in ports_to_scan):
        return Response(json.dumps({'error': '포트 목록은 정수형 배열이어야 합니다.'}), 
                      status=400, mimetype='application/json')
    
    # 스캔 전 호스트 이름을 IP로 변환
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return Response(json.dumps({'error': f"호스트 이름 '{host}'을(를) 확인할 수 없습니다."}), 
                      status=400, mimetype='application/json')
    
    # 포트 개수 제한
    if len(ports_to_scan) > 2000:
        return Response(json.dumps({'error': '한 번에 스캔할 수 있는 최대 포트 수는 2000개입니다.'}), 
                      status=400, mimetype='application/json')

    def generate_results():
        """포트를 스캔하고 결과를 생성하는 제너레이터 함수입니다."""
        total_ports = len(ports_to_scan)
        
        yield f"data: {json.dumps({'status': 'start', 'total': total_ports, 'host': host, 'ip': target_ip})}\n\n"
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
            future_to_port = {executor.submit(scan_port, target_ip, port): port for port in ports_to_scan}
            
            scanned_count = 0
            
            for future in concurrent.futures.as_completed(future_to_port):
                try:
                    data = future.result()
                    scanned_count += 1
                    
                    data['progress'] = {
                        'current': scanned_count,
                        'total': total_ports,
                        'percentage': round((scanned_count / total_ports) * 100, 1)
                    }
                    
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
        
        yield f"data: {json.dumps({'status': 'finished', 'total_scanned': scanned_count})}\n\n"

    response = Response(stream_with_context(generate_results()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response
    
@utils_bp.route('/api/dns-lookup/<domain_name>')
def dns_lookup(domain_name):
    """주어진 도메인 이름에 대한 DNS 조회를 수행합니다."""
    if not domain_name or not is_valid_host(domain_name):
        return jsonify({'error': '유효하지 않거나 비어있는 도메인 이름입니다.'}), 400

    try:
        results = socket.getaddrinfo(domain_name, None)
        ip_addresses = sorted(list(set(res[4][0] for res in results)))
        
        if not ip_addresses:
            return jsonify({'error': f"'{domain_name}'에 대한 IP 주소를 찾을 수 없습니다."}), 404
            
        return jsonify({
            'domain': domain_name,
            'ip_addresses': ip_addresses
        })
    except socket.gaierror:
        return jsonify({'error': f"호스트 이름 '{domain_name}'을(를) 확인할 수 없습니다."}), 404
    except Exception as e:
        current_app.logger.error(f"DNS 조회 중 오류 발생: {e}")
        return jsonify({'error': 'DNS 조회 중 서버 오류가 발생했습니다.'}), 500

@utils_bp.route('/api/utils/port_scan', methods=['GET'])
def api_port_scan():
    """API 형태의 포트 스캔 엔드포인트"""
    host = request.args.get('host')
    ports_str = request.args.get('ports', '')
    
    if not host:
        return jsonify({'error': '호스트를 지정해주세요.'}), 400
    
    if not is_valid_host(host):
        return jsonify({'error': '유효하지 않은 호스트입니다.'}), 400
    
    ports_to_scan = []
    try:
        for port_part in ports_str.split(','):
            port_part = port_part.strip()
            if '-' in port_part:
                start, end = map(int, port_part.split('-'))
                if start > end: 
                    start, end = end, start
                if end - start > 2000:
                    return jsonify({'error': '포트 범위가 너무 큽니다. 최대 2000개까지 가능합니다.'}), 400
                ports_to_scan.extend(range(start, end + 1))
            elif port_part:
                ports_to_scan.append(int(port_part))
    except ValueError:
        return jsonify({'error': '잘못된 포트 형식입니다.'}), 400
    
    ports_to_scan = sorted(list(set(ports_to_scan)))
    
    if len(ports_to_scan) > 2000:
        return jsonify({'error': '한 번에 스캔할 수 있는 최대 포트 수는 2000개입니다.'}), 400
    
    if not ports_to_scan:
        return jsonify({'error': '스캔할 포트를 지정해주세요.'}), 400
    
    try:
        target_ip = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({'error': f"호스트 '{host}'를 확인할 수 없습니다."}), 400
    
    results = {'host': host, 'ip': target_ip, 'open': [], 'closed': [], 'errors': []}
    
    for port in ports_to_scan[:100]:
        result = scan_port(target_ip, port)
        if result['error']: 
            results['errors'].append(port)
        elif result['status'] == 'Open': 
            results['open'].append(port)
        else: 
            results['closed'].append(port)
    
    return jsonify(results)