# app/routes/utils_routes.py
import socket
from flask import Blueprint, request, jsonify, current_app

utils_bp = Blueprint('utils', __name__, url_prefix='/api/utils')

def parse_ports(ports_str):
    """콤마로 구분된 포트 및 포트 범위 문자열을 파싱합니다."""
    ports = set()
    if not ports_str:
        return []
    
    for part in ports_str.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if 0 < start <= end < 65536:
                    ports.update(range(start, end + 1))
            except ValueError:
                continue # 잘못된 형식의 범위는 무시
        else:
            try:
                port = int(part)
                if 0 < port < 65536:
                    ports.add(port)
            except ValueError:
                continue # 정수가 아닌 부분은 무시
    return sorted(list(ports))

@utils_bp.route('/port_scan')
def port_scan():
    host = request.args.get('host')
    ports_str = request.args.get('ports')

    if not host:
        return jsonify({'error': '호스트가 필요합니다'}), 400
    
    ports_to_scan = parse_ports(ports_str)
    
    if not ports_to_scan:
        return jsonify({'error': '유효한 포트가 필요합니다'}), 400
        
    if len(ports_to_scan) > 100:
        return jsonify({'error': '포트가 너무 많습니다. 한 번에 100개 이하의 포트만 스캔해주세요.'}), 400

    open_ports = []
    closed_ports = []
    
    # 호스트 이름을 IP 주소로 먼저 변환
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify({'error': f"호스트를 확인할 수 없습니다: {host}"}), 404
        
    for port in ports_to_scan:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5) # 긴 대기를 피하기 위해 타임아웃 설정
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
        else:
            closed_ports.append(port)
        sock.close()
        
    return jsonify({
        'host': host,
        'ip': ip,
        'open': open_ports,
        'closed': closed_ports
    })
