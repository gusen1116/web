# app/__init__.py
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import os
from app.config import Config
import logging

# CSRF 보호 유지
csrf = CSRFProtect()

def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=False)
    
    # 로깅 설정
    if app.debug:
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    
    # 기본 설정
    app.config.from_object(Config)
    
    # 커스텀 설정 적용
    if config_object:
        app.config.from_object(config_object)
    
    # CSRF 보호 초기화
    csrf.init_app(app)
    
    # 블루프린트 등록
    from app.routes import main_routes, simulation, posts_routes
    
    app.register_blueprint(main_routes.main_bp)
    app.register_blueprint(simulation.simulation_bp)
    app.register_blueprint(posts_routes.posts_bp)
    
    # 콘텐츠 디렉토리 생성
    os.makedirs(app.config['POSTS_DIR'], exist_ok=True)
    
    # ===== 에러 핸들러 등록 =====
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403
    
    # 프로덕션 로깅
    if not app.debug:
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