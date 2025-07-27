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
from flask_assets import Environment, Bundle
from flask_caching import Cache

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
assets = Environment()
cache = Cache()  # Flask-Caching 추가

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

    # --- CSRF 설정 추가 (JSON 요청 처리를 위해) ---
    app.config['WTF_CSRF_EXEMPT_METHODS'] = []
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = False

    # --- Flask 확장 등록 ---
    compress.init_app(app)
    csrf.init_app(app)
    assets.init_app(app)
    cache.init_app(app)  # 캐시 초기화

    # --- CSS 번들 정의 및 등록 ---
    css_bundle = Bundle(
        'css/core.css',
        'css/components.css',
        'css/content.css',
        'css/layout-modules.css',
        'css/themes.css',
        'css/error-pages.css',
        filters='cssmin',
        output='gen/packed.css'
    )
    assets.register('all_css', css_bundle)
    
    # --- CSP Nonce 생성 ---
    @app.before_request
    def generate_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    # --- CSRF 토큰을 쿠키에 설정 (JavaScript에서 읽을 수 있도록) ---
    @app.after_request
    def set_csrf_cookie(response):
        """CSRF 토큰을 쿠키에 설정하여 JavaScript에서 접근 가능하게 함"""
        if 'csrf_token' not in g:
            from flask_wtf.csrf import generate_csrf
            generate_csrf()
        return response

    # --- Talisman 보안 설정 (안정성 강화) ---
    csp_config = app.config.get('CONTENT_SECURITY_POLICY')
    
    if app.config.get('DEBUG', False):
        if csp_config and 'connect-src' in csp_config:
            if isinstance(csp_config['connect-src'], list):
                if "'self'" not in csp_config['connect-src']:
                    csp_config['connect-src'].append("'self'")
            elif isinstance(csp_config['connect-src'], str):
                if "'self'" not in csp_config['connect-src']:
                    csp_config['connect-src'] = f"{csp_config['connect-src']} 'self'"
    
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
    
    # --- JSON 요청 처리를 위한 미들웨어 추가 ---
    @app.before_request
    def handle_json_request():
        if request.is_json:
            app.logger.debug(f"JSON 요청 수신: {request.path}")
    
    # --- 애플리케이션 시작 시 검증 작업 ---
    with app.app_context():
        verify_startup(app)
        # 검색 인덱스 초기화는 제거 (태그만 사용)
    
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
    from app.routes.gallery import gallery_bp  # 갤러리 블루프린트 추가
    from app.routes.posts_routes import posts_bp
    from app.routes.speedtest_routes import speedtest_bp
    from app.routes.whois_routes import whois_bp
    from app.routes.utils_routes import utils_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(gallery_bp)  # 갤러리 블루프린트 등록
    app.register_blueprint(posts_bp)
    app.register_blueprint(speedtest_bp)
    app.register_blueprint(whois_bp)
    app.register_blueprint(utils_bp)
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
    
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

def verify_startup(app):
    """애플리케이션 시작 시 검증 작업"""
    app.logger.info("애플리케이션 시작 검증...")
    
    with app.test_client() as client:
        response = client.options('/start_portscan')
        if response.status_code == 404:
            app.logger.warning("/start_portscan 엔드포인트를 찾을 수 없습니다!")
        else:
            app.logger.info("/start_portscan 엔드포인트 확인 완료")
    
    app.logger.info("애플리케이션 시작 검증 완료.")