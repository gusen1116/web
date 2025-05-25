# app/__init__.py
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
import os
import logging
from logging.handlers import RotatingFileHandler

# 전역 객체
csrf = CSRFProtect()
cache = Cache()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 설정 로드
    from app.config import config
    app.config.from_object(config[config_name])
    
    # 확장 초기화
    csrf.init_app(app)
    cache.init_app(app)
    
    # 필요한 디렉토리 생성
    ensure_directories(app)
    
    # 로깅 설정
    setup_logging(app)
    
    # 블루프린트 등록
    register_blueprints(app)
    
    # 에러 핸들러 등록
    register_error_handlers(app)
    
    return app

def ensure_directories(app):
    """필요한 디렉토리 생성"""
    directories = [
        app.config['CONTENT_DIR'],
        app.config['POSTS_DIR'],
        app.config['MEDIA_DIR'],
        app.config['IMAGES_DIR'],
        app.config['VIDEOS_DIR'],
        app.config['AUDIOS_DIR'],
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def setup_logging(app):
    """로깅 설정"""
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/wagusen.log', 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('와구센 블로그 시작')

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.main_routes import main_bp
    from app.routes.posts_routes import posts_bp
    from app.routes.simulation_routes import simulation_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(simulation_bp)

def register_error_handlers(app):
    """에러 핸들러 등록"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'서버 에러: {str(error)}')
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403