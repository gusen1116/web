from app import socketio

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시 호출"""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시 호출"""
    print('Client disconnected')