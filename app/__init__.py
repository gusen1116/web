# app/__init__.py
from flask import Flask, render_template
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
    
    # ===== 에러 핸들러 등록 =====
    
    @app.errorhandler(404)
    def not_found_error(error):
        """404 에러 처리"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 에러 처리"""
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """403 에러 처리"""
        return render_template('403.html'), 403
    
    # 개발 환경에서 에러 로깅
    if not app.debug:
        # 프로덕션 환경에서만 로깅
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/wagusen.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('와구센 애플리케이션 시작')
    
    return app