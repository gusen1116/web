# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # 기본 설정 - 절대 경로로 데이터베이스 위치 지정
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # 명시적 절대 경로로 데이터베이스 위치 지정
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'blog.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 디버깅을 위한 SQLAlchemy 로그 활성화
    import logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # 커스텀 설정 적용 (있다면)
    if config_object:
        app.config.from_object(config_object)
    
    # 확장 모듈 초기화
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # 모든 모델이 로드되었는지 확인
    with app.app_context():
        from app.models import User, Category, Tag, Post, PostTag
    
    # 블루프린트 등록
    from app.routes import main_routes, auth_routes, blog_routes, simulation
    app.register_blueprint(main_routes.main_bp)
    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(blog_routes.blog_bp)
    app.register_blueprint(simulation.simulation_bp)
    # app/__init__.py 파일에 추가
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 로그인 관리자 설정
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    return app