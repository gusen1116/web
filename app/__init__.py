# app/__init__.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import secrets
import importlib.util

from flask import Flask, g, request, render_template
from flask_compress import Compress
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

# --- 설정 파일 로드 (더 안정적인 방식으로 변경) ---
try:
    from app.app_config import config
except ImportError:
    print("CRITICAL ERROR: app/app_config.py 파일을 찾을 수 없습니다!", file=sys.stderr)
    sys.exit(1)

# --- Flask 확장 초기화 ---
compress = Compress()
talisman = Talisman()
csrf = CSRFProtect()

def create_app(config_name=None):
    """
    Flask 애플리케이션 팩토리 함수.
    """
    app = Flask(__name__)

    # --- 애플리케이션 설정 로드 ---
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)

    # --- Flask 확장 등록 ---
    compress.init_app(app)
    csrf.init_app(app)
    
    # --- CSP Nonce 생성 ---
    @app.before_request
    def generate_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    # --- Talisman 보안 설정 (안정성 강화) ---
    # app_config.py 에서 CSP 설정을 가져옵니다.
    csp_config = app.config.get('CONTENT_SECURITY_POLICY')
    
    # Flask-Talisman 초기화
    talisman.init_app(
        app,
        force_https=app.config.get('TALISMAN_FORCE_HTTPS', False),
        strict_transport_security=app.config.get('TALISMAN_HSTS_ENABLED', True),
        strict_transport_security_max_age=app.config.get('TALISMAN_HSTS_MAX_AGE', 31536000),
        content_security_policy=csp_config,
        content_security_policy_nonce_in=['script-src', 'style-src']
    )
    
    # --- 로깅 설정 ---
    setup_logging(app)
    
    # --- 블루프린트 등록 ---
    register_blueprints(app)
    
    # --- 에러 핸들러 등록 ---
    register_error_handlers(app)
    
    # --- 템플릿 필터 및 컨텍스트 프로세서 등록 ---
    register_template_helpers(app)
    
    # --- 애플리케이션 시작 시 검증 작업 ---
    with app.app_context():
        verify_startup(app)
    
    return app

def setup_logging(app):
    """애플리케이션 로깅 설정"""
    log_level_str = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    
    if app.config.get('LOG_TO_STDOUT', app.debug): 
        handler = logging.StreamHandler(sys.stdout)
    else:
        logs_dir = app.config.get('LOGS_DIR', 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        log_file_path = os.path.join(logs_dir, app.config.get('LOG_FILE', 'app.log'))
        max_bytes = app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024)
        backup_count = app.config.get('LOG_BACKUP_COUNT', 5)
        handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
    
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
    
    if not app.debug:
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.handlers.clear()
        werkzeug_logger.addHandler(handler)
        werkzeug_logger.setLevel(log_level)

    app.logger.info(f"애플리케이션 시작 (환경: {app.config.get('FLASK_ENV')})")

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes.main_routes import main_bp
    from app.routes.simulation import simulation_bp
    from app.routes.posts_routes import posts_bp
    from app.routes.speedtest_routes import speedtest_bp    
    
    app.register_blueprint(main_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(speedtest_bp)
    app.logger.info('모든 블루프린트 등록 완료')

def register_error_handlers(app):
    """에러 핸들러 등록"""
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'403 접근 금지: {request.url}')
        return render_template('403.html', error_message=str(error)), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f'404 페이지 찾을 수 없음: {request.url}')
        return render_template('404.html', error_message=str(error)), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        error_id = secrets.token_hex(8)
        app.logger.error(f'500 내부 서버 오류 (ID: {error_id}): {request.url} - {error}', exc_info=True)
        return render_template('500.html', error_id=error_id, error_message="서버 내부 오류 발생"), 500

def register_template_helpers(app):
    """템플릿 필터 및 컨텍스트 프로세서 등록"""
    @app.template_filter('dateformat')
    def dateformat_filter(value, format='%Y-%m-%d'):
        if value and hasattr(value, 'strftime'):
            return value.strftime(format)
        return ''
    
    @app.context_processor
    def inject_csp_nonce():
        return dict(csp_nonce=lambda: g.get('csp_nonce', ''))

def verify_startup(app):
    """애플리케이션 시작 시 검증 작업"""
    app.logger.info("애플리케이션 시작 검증...")
    # POSTS_DIR 검증 등 필요한 로직
    # ...
    app.logger.info("애플리케이션 시작 검증 완료.")