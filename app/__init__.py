# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
import os
from app.config import Config
from app.routes.visualization import register_visualization_routes
from app.services import socket_service

socketio = SocketIO()
csrf = CSRFProtect()

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    register_visualization_routes(app)    
    # 기본 설정은 Config 클래스에서 가져옴
    app.config.from_object(Config)
    
    # 커스텀 설정 적용 (있다면)
    if config_object:
        app.config.from_object(config_object)
    
    # 확장 모듈 초기화
    socketio.init_app(app)
    csrf.init_app(app)
    
    # 블루프린트 등록
    from app.routes import main_routes, simulation, posts_routes
    app.register_blueprint(main_routes.main_bp)
    app.register_blueprint(simulation.simulation_bp)
    app.register_blueprint(posts_routes.posts_bp)
    
    # 업로드 폴더 설정
    upload_folder = os.path.join(app.instance_path, 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    
    # 이미지, 텍스트, 파일 디렉토리 생성
    images_dir = os.path.join(upload_folder, 'images')
    texts_dir = os.path.join(upload_folder, 'texts')
    files_dir = os.path.join(upload_folder, 'files')
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(texts_dir, exist_ok=True)
    os.makedirs(files_dir, exist_ok=True)
    
    return app