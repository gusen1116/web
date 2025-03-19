# run.py
from app import create_app, socketio, db

app = create_app()

# 앱 컨텍스트에서 모델 임포트 확인
with app.app_context():
    from app.models import Category, Tag, Post, PostTag

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)