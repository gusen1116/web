# app/__init__.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import secrets
# hashlib 모듈은 현재 직접 사용되지 않으나, 추후 해시 관련 기능 추가 시 사용될 수 있습니다.
# import hashlib 
import importlib.util

from flask import Flask, g, request, render_template
from flask_compress import Compress
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

# --- 설정 파일 로드 ---
# 현재 파일(__init__.py)이 위치한 디렉토리 경로를 기준으로 app_config.py 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'app_config.py')

# app_config.py 파일을 동적으로 로드
# 이를 통해 app_config.py 내의 'config' 딕셔너리를 사용할 수 있게 됩니다.
spec = importlib.util.spec_from_file_location("app_config", config_path)
app_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config_module)
config = app_config_module.config # app_config.py 내의 config 딕셔너리 할당

# --- Flask 확장 초기화 ---
compress = Compress()
talisman = Talisman()
csrf = CSRFProtect()

def create_app(config_name=None):
    """
    Flask 애플리케이션 팩토리 함수.
    애플리케이션 인스턴스를 생성하고 각종 설정을 초기화합니다.
    """
    app = Flask(__name__)

    # --- 애플리케이션 설정 로드 ---
    # config_name이 주어지지 않으면 환경 변수 FLASK_CONFIG 또는 'default' 설정을 사용
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name]) # 선택된 설정 객체로부터 앱 설정을 로드
    if hasattr(config[config_name], 'init_app'): # 설정 객체에 init_app 메서드가 있다면 호출
        config[config_name].init_app(app)

    # --- Flask 확장 등록 ---
    compress.init_app(app) # 응답 압축 활성화
    csrf.init_app(app)     # CSRF 보호 활성화
    
    # --- CSP Nonce 생성 ---
    # 각 요청 전에 실행되어 Content Security Policy (CSP)를 위한 고유한 nonce를 생성합니다.
    # 이 nonce는 인라인 스크립트나 스타일을 안전하게 허용하는 데 사용됩니다.
    @app.before_request
    def generate_csp_nonce():
        """각 요청마다 고유한 CSP nonce를 생성하여 g 객체에 저장합니다."""
        g.csp_nonce = secrets.token_urlsafe(16)

    # --- Talisman 보안 설정 ---
    # HTTP 보안 헤더를 설정합니다 (예: HSTS, CSP).
    # Flask-Talisman 버전 호환성을 고려한 설정입니다.
    try:
        csp_string_from_config = app.config.get('SECURITY_HEADERS', {}).get('Content-Security-Policy', '')
        if '{nonce}' in csp_string_from_config:
            def get_nonce():
                return g.get('csp_nonce', '')
            
            csp_dict = _parse_csp_to_dict(csp_string_from_config)
            
            talisman.init_app(
                app,
                force_https=app.config.get('TALISMAN_FORCE_HTTPS', False), # 개발 환경에서는 False 권장
                strict_transport_security=app.config.get('TALISMAN_HSTS_ENABLED', True),
                strict_transport_security_max_age=app.config.get('TALISMAN_HSTS_MAX_AGE', 31536000),
                content_security_policy=csp_dict,
                content_security_policy_nonce_in=['script-src', 'style-src'],
                content_security_policy_nonce_func=get_nonce
            )
        else:
            parsed_csp = _parse_csp_to_dict(csp_string_from_config) if csp_string_from_config else None
            talisman.init_app(
                app,
                force_https=app.config.get('TALISMAN_FORCE_HTTPS', False),
                strict_transport_security=app.config.get('TALISMAN_HSTS_ENABLED', True),
                strict_transport_security_max_age=app.config.get('TALISMAN_HSTS_MAX_AGE', 31536000),
                content_security_policy=parsed_csp
            )
    except TypeError:
        app.logger.warning("Flask-Talisman의 최신 버전 API를 사용할 수 없어 구버전 방식으로 CSP를 설정합니다. CSP 설정이 하드코딩될 수 있습니다.")
        talisman.init_app(
            app,
            force_https=False,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={ # 구버전 Talisman을 위한 하드코딩된 CSP (nonce 미지원)
                'default-src': ["'self'"],
                'script-src': ["'self'", "'unsafe-inline'", 'https://www.youtube.com', 'https://youtube.com'],
                'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com', 'https://cdnjs.cloudflare.com'],
                'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
                'img-src': ["'self'", 'data:', 'https:'], # 모든 HTTPS 이미지 허용
                'frame-src': ["'self'", 'https://www.youtube.com', 'https://youtube.com']
            }
        )
    
    # --- 로깅 설정 ---
    setup_logging(app)
    
    # --- 블루프린트 등록 ---
    register_blueprints(app)
    
    # --- 에러 핸들러 등록 ---
    register_error_handlers(app)
    
    # --- 템플릿 필터 등록 ---
    register_template_filters(app)
    
    # --- 애플리케이션 시작 시 검증 작업 ---
    with app.app_context():
        verify_startup(app)
    
    return app

def _parse_csp_to_dict(csp_string):
    """
    CSP 문자열을 Flask-Talisman이 이해할 수 있는 딕셔너리 형태로 변환합니다.
    예: "default-src 'self'; script-src 'self' example.com" -> {'default-src': ["'self'"], 'script-src': ["'self'", "example.com"]}
    """
    csp_dict = {}
    if not csp_string:
        return csp_dict
        
    directives = csp_string.split(';')
    for directive_entry in directives:
        directive_entry = directive_entry.strip()
        if not directive_entry:
            continue
        
        parts = directive_entry.split(None, 1) # 지시어와 값 부분을 분리 (예: "script-src"와 "'self' example.com")
        if not parts:
            continue

        key = parts[0].lower() # 지시어는 소문자로 (예: "script-src")
        
        if len(parts) > 1:
            values_str = parts[1]
            # 값들을 공백으로 분리. 따옴표로 묶인 값은 하나의 단위로 취급 (간단한 파서)
            # CSP 값은 공백으로 구분되므로, shlex.split과 유사하게 동작하도록 시도
            import shlex
            try:
                # shlex.split은 쉘과 유사한 방식으로 문자열을 분리하여 따옴표 등을 올바르게 처리
                values = shlex.split(values_str)
            except ValueError:
                # shlex 파싱 실패 시 단순 공백 분할 (예외적인 경우)
                values = values_str.split()

            # Talisman은 nonce를 content_security_policy_nonce_func를 통해 자동으로 처리하므로,
            # 여기서 '{nonce}' 플레이스홀더를 직접 다룰 필요는 없습니다.
            # 필요한 경우, Talisman 설정에서 nonce가 적용될 지시어(directive)만 지정합니다.
            final_values = [v for v in values if '{nonce}' not in v] # {nonce}는 Talisman이 관리
            
            if final_values:
                 csp_dict[key] = final_values
            elif key: 
                 csp_dict[key] = [] # 지시어만 있고 값이 없는 경우 (예: 'upgrade-insecure-requests')
        elif key: # 값 없이 지시어만 있는 경우
            csp_dict[key] = []
    return csp_dict

def setup_logging(app):
    """
    애플리케이션 로깅을 설정합니다.
    - 운영 환경에서는 JSON 형식 또는 표준 형식을 사용할 수 있습니다.
    - 파일 또는 STDOUT으로 로깅할 수 있습니다.
    - 멀티프로세스 환경을 고려하여 WatchedFileHandler 또는 RotatingFileHandler를 사용합니다.
    """
    log_level_str = app.config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # 기존 핸들러 제거 (Flask의 기본 핸들러 또는 이전 핸들러와의 중복 방지)
    if app.logger.hasHandlers():
        app.logger.handlers.clear()

    # 포맷터 설정
    # JSON_LOGGING 설정이 True이고 운영 환경일 때 JSON 포맷 사용
    if app.config.get('FLASK_ENV') == 'production' and app.config.get('JSON_LOGGING', False):
        formatter = logging.Formatter(
            '{"time":"%(asctime)s", "level":"%(levelname)s", "module":"%(module)s", '
            '"func":"%(funcName)s", "line":%(lineno)d, "message":"%(message)s"}'
        )
    else: # 그 외의 경우 (개발 환경 또는 JSON 로깅 비활성화 시) 일반 텍스트 포맷 사용
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

    # 핸들러 설정 (STDOUT 또는 파일)
    # LOG_TO_STDOUT 설정이 True이거나, 개발 모드일 때 STDOUT으로 로깅
    if app.config.get('LOG_TO_STDOUT', app.debug): 
        handler = logging.StreamHandler(sys.stdout)
    else: # 파일 로깅 설정
        logs_dir = app.config.get('LOGS_DIR', 'logs') # 로그 파일 저장 디렉토리
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir)
            except OSError as e:
                # 로그 디렉토리 생성 실패 시, 에러를 로깅하고 STDOUT으로 대체
                # 이 시점에서는 app.logger에 핸들러가 없을 수 있으므로 print 사용
                print(f"ERROR: 로그 디렉토리 생성 실패: {logs_dir}, 오류: {e}. STDOUT으로 로깅합니다.", file=sys.stderr)
                handler = logging.StreamHandler(sys.stdout)
        
        # 'handler'가 위에서 설정되지 않았다면 (즉, 로그 디렉토리 생성 성공 시) 파일 핸들러 설정
        if 'handler' not in locals(): 
            log_file_path = os.path.join(logs_dir, app.config.get('LOG_FILE', 'app.log'))
            # 멀티프로세스 환경이고 Windows가 아닐 경우 WatchedFileHandler 사용 (파일 변경 감지)
            if app.config.get('MULTIPROCESS_LOGGING', False) and not sys.platform.startswith("win"):
                handler = WatchedFileHandler(log_file_path)
            else: # 그 외에는 RotatingFileHandler 사용 (파일 크기 기반 로테이션)
                max_bytes = app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024) # 기본 10MB
                backup_count = app.config.get('LOG_BACKUP_COUNT', 5) # 기본 5개 백업
                handler = RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count)
    
    handler.setFormatter(formatter) # 핸들러에 포맷터 적용
    handler.setLevel(log_level)     # 핸들러에 로깅 레벨 적용
    
    app.logger.addHandler(handler)  # Flask 앱 로거에 핸들러 추가
    app.logger.setLevel(log_level)  # Flask 앱 로거 레벨 설정
    
    # 운영 환경에서는 Werkzeug 로거 (Flask 내부 웹 서버 로거)에도 동일한 핸들러와 레벨 적용
    if not app.debug: 
        werkzeug_logger = logging.getLogger('werkzeug')
        if werkzeug_logger.hasHandlers(): # Werkzeug 로거도 기존 핸들러 제거
            werkzeug_logger.handlers.clear()
        werkzeug_logger.addHandler(handler)
        werkzeug_logger.setLevel(log_level)

    app.logger.info(f"애플리케이션 시작 (환경: {app.config.get('FLASK_ENV')}, 로깅 레벨: {log_level_str})")


def register_blueprints(app):
    """블루프린트를 애플리케이션에 등록합니다."""
    # app.routes 패키지의 __init__.py 파일에서 정의된 블루프린트들을 가져옵니다.
    # 이 단계에서 ImportError가 발생한다면 app/routes/__init__.py 파일에 문제가 있는 것입니다.
    from app.routes.main_routes import main_bp
    from app.routes.simulation import simulation_bp
    from app.routes.posts_routes import posts_bp
    from app.routes.speedtest_routes import speedtest_bp    
    
    app.register_blueprint(main_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(speedtest_bp) 
    __all__ = ['main_bp', 'simulation_bp', 'posts_bp', 'speedtest_bp']
    app.logger.info('모든 블루프린트가 성공적으로 등록되었습니다.')

def register_error_handlers(app):
    """HTTP 에러 핸들러를 애플리케이션에 등록합니다."""
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(
            f'403 접근 금지: {request.url} (User-Agent: {request.headers.get("User-Agent")})', 
            exc_info=error # 예외 정보 로깅
        )
        return render_template('403.html', error_message=str(error)), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(
            f'404 페이지 찾을 수 없음: {request.url} (User-Agent: {request.headers.get("User-Agent")})'
        )
        return render_template('404.html', error_message=str(error)), 404
    
    @app.errorhandler(500)
    def internal_server_error(error): # 함수 이름 변경 (internal_error -> internal_server_error)
        error_id = secrets.token_hex(8) # 각 에러에 대한 고유 ID 생성
        app.logger.error(
            f'500 내부 서버 오류 (ID: {error_id}): {request.url} - {error}', 
            exc_info=True # 전체 트레이스백 로깅
        )
        # 사용자에게는 일반적인 오류 메시지와 에러 ID만 전달
        return render_template('500.html', error_id=error_id, error_message="서버 내부에서 오류가 발생했습니다."), 500

def register_template_filters(app):
    """Jinja2 템플릿에서 사용할 커스텀 필터를 등록합니다."""
    @app.template_filter('dateformat')
    def dateformat_filter(value, format='%Y-%m-%d'): # 필터 이름 명확히 (dateformat -> dateformat_filter)
        if value and hasattr(value, 'strftime'): # datetime 객체인지 확인
            return value.strftime(format)
        return '' # 유효하지 않은 값이면 빈 문자열 반환
    
    @app.template_filter('readtime')
    def readtime_filter(word_count): # 필터 이름 명확히 (readtime -> readtime_filter)
        if not isinstance(word_count, (int, float)) or word_count < 0:
            return "0분"
        # 분당 평균 200-250 단어를 읽는다고 가정
        minutes_to_read = max(1, round(word_count / 225)) 
        return f"{minutes_to_read}분"
    
    @app.template_filter('truncate_text')
    def truncate_text_filter(text, length=100, suffix='...'): # 필터 이름 명확히 (truncate_text -> truncate_text_filter)
        if not isinstance(text, str):
            return ''
        if len(text) <= length:
            return text
        
        # 접미사 길이를 고려하여 자를 위치 계산
        adjusted_length = length - len(suffix)
        if adjusted_length <= 0: # 접미사가 길이보다 길거나 같으면 접미사만 반환 (또는 예외 처리)
            return suffix

        # 단어 경계에서 자르기 시도
        truncated_part = text[:adjusted_length]
        last_space = truncated_part.rfind(' ')
        
        if last_space != -1: # 마지막 공백이 있다면 거기까지 자름
            return truncated_part[:last_space] + suffix
        else: # 공백이 없다면 그냥 길이만큼 자름 (단어가 매우 긴 경우)
            return truncated_part + suffix
    
    # CSP nonce를 템플릿 컨텍스트에 주입하는 함수
    @app.context_processor
    def inject_csp_nonce_to_context():
        # g.csp_nonce가 설정되지 않았을 경우 (예: 요청 컨텍스트 외부) 빈 문자열 반환
        return dict(csp_nonce=lambda: g.get('csp_nonce', ''))


def verify_startup(app):
    """애플리케이션 시작 시 주요 설정 및 디렉토리 존재 여부를 검증합니다."""
    app.logger.info("애플리케이션 시작 검증 중...")

    # POSTS_DIR 검증
    posts_dir = app.config.get('POSTS_DIR')
    if not posts_dir:
        app.logger.error('CRITICAL: POSTS_DIR 설정이 누락되었습니다. 포스트 기능을 사용할 수 없습니다.')
    elif not os.path.exists(posts_dir):
        app.logger.warning(f'포스트 디렉토리가 존재하지 않습니다: {posts_dir}')
        try:
            os.makedirs(posts_dir)
            app.logger.info(f'포스트 디렉토리 생성 완료: {posts_dir}')
        except Exception as e:
            app.logger.error(f'포스트 디렉토리 생성 실패: {e}')
    else:
        app.logger.info(f'포스트 디렉토리 확인: {posts_dir}')
    
    # 시뮬레이션 템플릿 검증
    try:
        simulation_module_path = os.path.join(os.path.dirname(__file__), 'routes', 'simulation.py')
        if os.path.exists(simulation_module_path):
            from app.routes.simulation import verify_simulation_templates
            if callable(verify_simulation_templates):
                verify_simulation_templates(app) # app 객체 전달
            else:
                app.logger.warning('verify_simulation_templates 함수를 찾을 수 없거나 호출할 수 없습니다.')
        else:
            app.logger.info('시뮬레이션 라우트 모듈(simulation.py)을 찾을 수 없습니다. 관련 기능이 제한될 수 있습니다.')
    except ImportError:
        app.logger.info('시뮬레이션 관련 모듈(app.routes.simulation)을 가져오는 데 실패했습니다.')
    except Exception as e:
        app.logger.error(f'시뮬레이션 템플릿 검증 중 예기치 않은 오류 발생: {e}')
    
    # 정적 미디어 디렉토리 검증 및 생성
    static_dirs = app.config.get('STATIC_MEDIA_DIRS', ['img', 'videos', 'audios'])
    if app.static_folder and os.path.isdir(app.static_folder): # static_folder 존재 및 디렉토리 여부 확인
        for dir_name in static_dirs:
            dir_path = os.path.join(app.static_folder, dir_name)
            if not os.path.exists(dir_path):
                app.logger.warning(f'정적 미디어 디렉토리가 존재하지 않습니다: {dir_path}')
                try:
                    os.makedirs(dir_path)
                    app.logger.info(f'정적 미디어 디렉토리 생성 완료: {dir_path}')
                except Exception as e:
                    app.logger.error(f'정적 미디어 디렉토리 ({dir_name}) 생성 실패: {e}')
            else:
                app.logger.info(f'정적 미디어 디렉토리 확인: {dir_path}')

    else:
        app.logger.warning(
            f"Flask app.static_folder ('{app.static_folder}')가 설정되지 않았거나 유효한 디렉토리가 아닙니다. "
            "정적 미디어 디렉토리를 확인할 수 없습니다."
        )

    # 캐시 서비스 초기화
    try:
        cache_service_module_path = os.path.join(os.path.dirname(__file__), 'services', 'cache_service.py')
        if os.path.exists(cache_service_module_path):
            from app.services.cache_service import CacheService
            CacheService.configure(
                cache_timeout=app.config.get('CACHE_TIMEOUT'),
                max_size=app.config.get('CACHE_MAX_SIZE')
            )
            app.logger.info('캐시 서비스 설정 완료.')
        else:
            app.logger.info('CacheService 모듈(cache_service.py)을 찾을 수 없어 초기화를 건너뜁니다.')
    except ImportError:
        app.logger.warning('app.services.cache_service 모듈을 가져오는 데 실패했습니다. 캐시 서비스가 비활성화될 수 있습니다.')
    except Exception as e:
        app.logger.error(f'캐시 서비스 초기화 중 예기치 않은 오류 발생: {e}')
    
    app.logger.info("애플리케이션 시작 검증 완료.")


def get_locale():
    """
    요청 헤더를 기반으로 사용자의 최적 로케일을 결정합니다.
    지원되는 언어 목록과 기본 로케일은 설정을 통해 관리됩니다.
    """
    supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', ['ko', 'en'])  # noqa: F821
    default_locale = current_app.config.get('DEFAULT_LOCALE', 'ko')  # noqa: F821
    
    # request 객체가 있는 경우 (즉, HTTP 요청 컨텍스트 내)에만 accept_languages 사용
    if request:
        return request.accept_languages.best_match(supported_languages, default=default_locale)
    
    # 요청 컨텍스트가 없는 경우 (예: 백그라운드 작업, CLI 명령) 기본 로케일 반환
    return default_locale