# app/__init__.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import secrets

from flask import Flask, g, request, render_template, url_for
from flask_compress import Compress
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect
from flask_assets import Environment, Bundle
from werkzeug.utils import safe_join

# --- Load configuration safely ---
try:
    from app.app_config import config
except ImportError:
    print("CRITICAL ERROR: app/app_config.py 파일을 찾을 수 없습니다!", file=sys.stderr)
    sys.exit(1)

# --- Initialize Flask extensions ---
compress = Compress()
talisman = Talisman()
csrf = CSRFProtect()
assets = Environment()

def page_not_found(e):
    return render_template('404.html'), 404

def internal_server_error(e):
    return render_template('500.html'), 500

def create_app(config_name: str | None = None) -> Flask:
    """Application factory function."""
    
    # 명시적으로 정적 및 템플릿 폴더의 절대 경로를 계산합니다.
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(APP_DIR, 'static')
    template_dir = os.path.join(APP_DIR, 'templates')

    app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)

    # --- Load application settings ---
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)

    # --- CSRF settings for JSON requests ---
    app.config['WTF_CSRF_EXEMPT_METHODS'] = []
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = False

    # --- Register Flask extensions ---
    compress.init_app(app)
    csrf.init_app(app)
    assets.init_app(app)

    # --- CSS & JS bundling ---
    js_bundle = Bundle(
        'js/main.js',
        'js/slide-minimal.js',
        filters='jsmin',
        output='gen/packed.js'
    )
    assets.register('all_js', js_bundle)


    # --- Generate CSP nonce on each request ---
    @app.before_request
    def generate_csp_nonce() -> None:
        g.csp_nonce = secrets.token_urlsafe(16)

    # --- Ensure CSRF token is available as a cookie for JS ---
    @app.after_request
    def set_csrf_cookie(response):
        if 'csrf_token' not in g:
            from flask_wtf.csrf import generate_csrf
            generate_csrf()
        return response

    # --- Configure Content Security Policy ---
    csp_config = app.config.get('CSP', {})

    talisman.init_app(
        app,
        force_https=app.config.get('TALISMAN_FORCE_HTTPS', False),
        strict_transport_security=app.config.get('TALISMAN_HSTS_ENABLED', True),
        strict_transport_security_max_age=app.config.get('TALISMAN_HSTS_MAX_AGE', 31536000),
        content_security_policy=csp_config,
    )

    # --- Setup logging ---
    setup_logging(app)

    # --- Register blueprints ---
    from app.routes.main_routes import main_bp
    from app.routes.gallery import gallery_bp
    from app.routes.posts_routes import posts_bp
    from app.routes.speedtest_routes import speedtest_bp
    from app.routes.whois_routes import whois_bp
    from app.routes.utils_routes import utils_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(speedtest_bp)
    app.register_blueprint(whois_bp)
    app.register_blueprint(utils_bp)

    # --- Register error handlers ---
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    register_template_helpers(app)

    # --- Middleware for JSON requests ---
    @app.before_request
    def handle_json_request() -> None:
        if request.is_json:
            app.logger.debug(f"JSON 요청 수신: {request.path}")

    # --- Perform startup validation within an application context ---
    with app.app_context():
        verify_startup(app)

    return app

def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level_str = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    if app.config.get('LOG_TO_STDOUT', app.debug):
        handler = logging.StreamHandler(sys.stdout)
    else:
        logs_dir = app.config.get('LOGS_DIR', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
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

def register_template_helpers(app: Flask) -> None:
    """Register custom template filters and context processors."""
    @app.template_filter('dateformat')
    def dateformat_filter(value, format: str = '%Y-%m-%d'):
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

    @app.context_processor
    def inject_static_url():
        def static_url(filename: str) -> str:
            """Return a cache-busted static asset URL based on file mtime."""
            version = None
            try:
                file_path = safe_join(app.static_folder, filename)
                if file_path:
                    version = int(os.path.getmtime(file_path))
            except (OSError, TypeError, ValueError):
                version = None
            if version:
                return url_for('static', filename=filename, v=version)
            return url_for('static', filename=filename)

        return dict(static_url=static_url)

def verify_startup(app: Flask) -> None:
    """Perform simple checks when the application starts."""
    app.logger.info("애플리케이션 시작 검증...")
    with app.test_client() as client:
        response = client.options('/start_portscan')
        if response.status_code == 404:
            app.logger.warning("/start_portscan 엔드포인트를 찾을 수 없습니다!")
        else:
            app.logger.info("/start_portscan 엔드포인트 확인 완료")
    app.logger.info("애플리케이션 시작 검증 완료.")
