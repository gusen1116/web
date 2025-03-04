# app/services/socket_service.py
from flask_socketio import SocketIO, emit
from app import socketio

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('raspberry_data')
def handle_raspberry_data(data):
    # 라즈베리파이에서 전송된 데이터 처리
    print(f'Received data: {data}')
    # 클라이언트에 데이터 전송
    emit('update_data', data, broadcast=True)