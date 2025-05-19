# app/__init__.py
from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
from app.config import Config
import logging

# CSRF 보호 유지
csrf = CSRFProtect()

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # 로깅 설정 추가
    if app.debug:
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        app.logger.debug("디버그 모드로 애플리케이션 실행 중")
    
    # 기본 설정은 Config 클래스에서 가져옴
    app.config.from_object(Config)
    
    # 커스텀 설정 적용 (있다면)
    if config_object:
        app.config.from_object(config_object)
    
    # CSRF 보호 초기화
    csrf.init_app(app)
    
    # 블루프린트 등록
    from app.routes import main_routes, simulation, posts_routes
    
    app.register_blueprint(main_routes.main_bp)
    app.register_blueprint(simulation.simulation_bp)
    app.register_blueprint(posts_routes.posts_bp)
    
    # 기존 폴더 구조 유지 (uploads 폴더를 기본으로 사용)
    upload_folder = os.path.join(app.instance_path, 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    
    # 필요한 디렉토리 생성
    texts_dir = os.path.join(upload_folder, 'texts')
    images_dir = os.path.join(upload_folder, 'images')
    videos_dir = os.path.join(upload_folder, 'videos')
    audios_dir = os.path.join(upload_folder, 'audios')
    files_dir = os.path.join(upload_folder, 'files')
    os.makedirs(files_dir, exist_ok=True)
    os.makedirs(texts_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(audios_dir, exist_ok=True)
    
    return app