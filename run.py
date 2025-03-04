# run.py
# 앱 생성 함수를 직접 정의
from flask import Flask
from flask_socketio import SocketIO

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    # 기타 설정...
    return app

app = create_app()
socketio = SocketIO(app)

# 라우트 등록
from app.routes import main_routes, auth_routes, blog_routes
app.register_blueprint(main_routes.main_bp)
app.register_blueprint(auth_routes.auth_bp)
app.register_blueprint(blog_routes.blog_bp)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)