# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()

def create_app(config_object='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # 확장 모듈 초기화
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    
    # 라우트 등록
    from app.routes import auth, blog, simulation, main
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(blog.blog_bp)
    app.register_blueprint(simulation.simulation_bp)
    app.register_blueprint(main.main_bp)
    
    # 로그인 관리자 설정
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    return app