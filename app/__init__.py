# app/__init__.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler, WatchedFileHandler
import secrets
import hashlib
import importlib.util

from flask import Flask, g, request
from flask_compress import Compress
from flask_talisman import Talisman

# 로컬 app_config.py를 강제로 로드 (app 디렉토리 내부에 있음)
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'app_config.py')

# app_config.py 파일을 직접 로드
spec = importlib.util.spec_from_file_location("app_config", config_path)
app_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config)

# config 딕셔너리 가져오기
config = app_config.config

compress = Compress()
talisman = Talisman()

def create_app(config_name=None):
    """애플리케이션 팩토리 패턴 - 보안 및 성능 개선"""
    app = Flask(__name__)
    
    # 설정 로드
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 확장 초기화
    compress.init_app(app)
    
    # CSP nonce 생성을 위한 before_request 핸들러
    @app.before_request
    def generate_csp_nonce():
        """각 요청마다 고유한 CSP nonce 생성"""
        g.csp_nonce = secrets.token_urlsafe(16)
    
    # Talisman 보안 설정 - 버전 호환성 처리
    try:
        # 최신 버전 시도
        csp = app.config['SECURITY_HEADERS'].get('Content-Security-Policy', '')
        if '{nonce}' in csp:
            # nonce 기반 CSP 사용
            def get_nonce():
                return g.get('csp_nonce', '')
            
            # CSP에서 {nonce} 플레이스홀더를 실제 nonce로 교체
            csp_dict = _parse_csp_to_dict(csp)
            
            talisman.init_app(
                app,
                force_https=False,  # 리버스 프록시 뒤에서 실행 가정
                strict_transport_security=True,
                strict_transport_security_max_age=31536000,
                content_security_policy=csp_dict,
                content_security_policy_nonce_in=['script-src', 'style-src'],
                content_security_policy_nonce_func=get_nonce
            )
        else:
            # 기본 CSP 사용
            talisman.init_app(
                app,
                force_https=False,
                strict_transport_security=True,
                strict_transport_security_max_age=31536000
            )
    except TypeError:
        # 구버전 Flask-Talisman 대응
        # nonce 지원 없이 기본 설정만 사용
        talisman.init_app(
            app,
            force_https=False,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            content_security_policy={
                'default-src': ["'self'"],
                'script-src': ["'self'", "'unsafe-inline'", 'https://www.youtube.com', 'https://youtube.com'],
                'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com', 'https://cdnjs.cloudflare.com'],
                'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
                'img-src': ["'self'", 'data:', 'https:'],
                'frame-src': ["'self'", 'https://www.youtube.com', 'https://youtube.com']
            }
        )
    
    # 로깅 설정 개선
    setup_logging(app)
    
    # 블루프린트 등록
    register_blueprints(app)
    
    # 에러 핸들러 등록
    register_error_handlers(app)
    
    # 템플릿 필터 등록
    register_template_filters(app)
    
    # 시작 시 검증
    with app.app_context():
        verify_startup(app)
    
    return app

def _parse_csp_to_dict(csp_string):
    """CSP 문자열을 Talisman이 사용할 수 있는 딕셔너리로 변환"""
    csp_dict = {}
    directives = csp_string.split(';')
    
    for directive in directives:
        directive = directive.strip()
        if not directive:
            continue
            
        parts = directive.split()
        if len(parts) >= 2:
            key = parts[0]
            values = parts[1:]
            
            # {nonce} 플레이스홀더 제거 (Talisman이 자동으로 추가)
            values = [v for v in values if '{nonce}' not in v]
            
            # 'self'를 "'self'"로 변환
            values = ["'self'" if v == 'self' else v for v in values]
            
            csp_dict[key] = values
    
    return csp_dict

def setup_logging(app):
    """향상된 로깅 설정 - 멀티프로세스 환경 지원"""
    if not app.debug and not app.testing:
        # 로그 레벨 설정
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
        
        # stdout 로깅 (권장)
        if app.config.get('LOG_TO_STDOUT'):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            
            # 구조화된 로그 포맷
            if app.config.get('FLASK_ENV') == 'production':
                # 프로덕션: JSON 형식 로그 (로그 수집 시스템 연동 용이)
                formatter = logging.Formatter(
                    '{"time":"%(asctime)s", "level":"%(levelname)s", '
                    '"module":"%(module)s", "func":"%(funcName)s", '
                    '"message":"%(message)s"}'
                )
            else:
                # 개발: 읽기 쉬운 형식
                formatter = logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s '
                    '[in %(pathname)s:%(lineno)d]'
                )
            
            stream_handler.setFormatter(formatter)
            app.logger.addHandler(stream_handler)
        else:
            # 파일 로깅 - WatchedFileHandler 사용 (외부 로그 로테이션 지원)
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            # 프로세스별 로그 파일 (멀티프로세스 환경 대응)
            if app.config.get('MULTIPROCESS_LOGGING', False):
                log_filename = f'logs/app-{os.getpid()}.log'
                file_handler = WatchedFileHandler(log_filename)
            else:
                # 단일 프로세스 또는 외부 로그 로테이션 사용 시
                file_handler = WatchedFileHandler('logs/app.log')
            
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
            ))
            app.logger.addHandler(file_handler)
        
        app.logger.setLevel(log_level)
        app.logger.info('애플리케이션 시작')

def register_blueprints(app):
    """블루프린트 등록"""
    from app.routes import main_bp, simulation_bp, posts_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(posts_bp)
    
    app.logger.info('블루프린트 등록 완료')

def register_error_handlers(app):
    """전역 에러 핸들러 등록"""
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        app.logger.info(f'404 에러: {request.url}')
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        app.logger.error(f'500 에러: {error}')
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        app.logger.warning(f'403 에러: {request.url}')
        return render_template('403.html'), 403

def register_template_filters(app):
    """템플릿 필터 등록"""
    @app.template_filter('dateformat')
    def dateformat(value, format='%Y-%m-%d'):
        """날짜 형식 필터"""
        if value:
            return value.strftime(format)
        return ''
    
    @app.template_filter('readtime')
    def readtime(word_count):
        """읽기 시간 계산 필터"""
        # 평균 읽기 속도: 분당 200-250 단어
        minutes = max(1, round(word_count / 225))
        return f"{minutes}분"
    
    @app.template_filter('truncate_text')
    def truncate_text(text, length=100):
        """텍스트 자르기 필터"""
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + '...'
    
    # CSP nonce를 템플릿에서 사용할 수 있도록
    @app.context_processor
    def inject_csp_nonce():
        return dict(csp_nonce=lambda: g.get('csp_nonce', ''))

def verify_startup(app):
    """애플리케이션 시작 시 검증"""
    # 포스트 디렉토리 확인
    posts_dir = app.config.get('POSTS_DIR')
    if not os.path.exists(posts_dir):
        app.logger.warning(f'포스트 디렉토리가 존재하지 않습니다: {posts_dir}')
        try:
            os.makedirs(posts_dir)
            app.logger.info(f'포스트 디렉토리 생성: {posts_dir}')
        except Exception as e:
            app.logger.error(f'포스트 디렉토리 생성 실패: {e}')
    
    # 시뮬레이션 템플릿 검증
    try:
        from app.routes.simulation import verify_simulation_templates
        verify_simulation_templates(app)
    except Exception as e:
        app.logger.error(f'시뮬레이션 템플릿 검증 실패: {e}')
    
    # 정적 파일 디렉토리 검증
    static_dirs = ['img', 'videos', 'audios']
    for dir_name in static_dirs:
        dir_path = os.path.join(app.static_folder, dir_name)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                app.logger.info(f'정적 디렉토리 생성: {dir_path}')
            except Exception as e:
                app.logger.error(f'정적 디렉토리 생성 실패: {e}')
    
    # 캐시 서비스 초기화
    try:
        from app.services.cache_service import CacheService
        CacheService.configure(
            cache_timeout=app.config.get('CACHE_TIMEOUT'),
            max_size=app.config.get('CACHE_MAX_SIZE')
        )
        app.logger.info('캐시 서비스 초기화 완료')
    except Exception as e:
        app.logger.error(f'캐시 서비스 초기화 실패: {e}')

# 헬퍼 함수들
def get_locale():
    """사용자 로케일 감지"""
    return request.accept_languages.best_match(['ko', 'en']) or 'ko'