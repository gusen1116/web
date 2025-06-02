# app_config.py
import os
import sys
from datetime import timedelta
from pathlib import Path

# 베이스 디렉토리
basedir = Path(__file__).parent.parent.resolve()

class Config:
    """향상된 보안 설정을 가진 기본 설정 클래스"""
    
    # 환경 변수를 통한 SECRET_KEY 강제
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 프로덕션 환경에서 SECRET_KEY 검증
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    
    # 프로덕션 환경에서 SECRET_KEY 미설정시 에러
    if not SECRET_KEY and FLASK_ENV == 'production' and not FLASK_DEBUG:
        print("CRITICAL ERROR: SECRET_KEY 환경 변수가 프로덕션 환경에서 설정되지 않았습니다!", file=sys.stderr)
        sys.exit(1)
    elif not SECRET_KEY:
        # 개발 환경용 경고 및 기본값
        print("WARNING: 개발 환경용 기본 SECRET_KEY를 사용합니다. 프로덕션에서는 절대 사용하지 마세요!")
        SECRET_KEY = 'dev-only-secret-key-do-not-use-in-production'
    
    # 세션 설정 - 보안 강화
    SESSION_COOKIE_SECURE = True  # HTTPS 전용
    SESSION_COOKIE_HTTPONLY = True  # JavaScript 접근 차단
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF 방어
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 세션 수명
    
    # 보안 헤더 설정 강화
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        # CSP는 nonce 기반으로 변경 (unsafe-inline, unsafe-eval 제거)
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'nonce-{nonce}' https://www.youtube.com https://youtube.com; "
            "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "frame-src 'self' https://www.youtube.com https://youtube.com; "
            "connect-src 'self'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'self'; "
            "object-src 'none'; "
            "upgrade-insecure-requests"
        )
    }
    
    # 파일 및 콘텐츠 설정
    POSTS_DIR = os.environ.get('POSTS_DIR', str(basedir / 'posts'))
    ALLOWED_TEXT_EXTENSIONS = {'txt', 'md'}
    MAX_FILE_READ_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 콘텐츠 제한
    MAX_TITLE_LENGTH = 200
    MAX_TAG_LENGTH = 50
    MAX_TAGS_PER_POST = 15
    MAX_PREVIEW_LENGTH = 300
    MAX_POSTS_TOTAL = 2000
    
    # 캐시 설정
    CACHE_TIMEOUT = 600  # 10분
    CACHE_MAX_SIZE = 1000
    
    # 마크다운 설정
    MARKDOWN_EXTENSIONS = [
        'extra', 'nl2br', 'sane_lists', 'codehilite', 'toc'
    ]
    
    # 허용된 HTML 태그 및 속성
    ALLOWED_HTML_TAGS = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'hr', 'a', 'strong', 'em',
        'code', 'pre', 'blockquote', 'img',
        'ul', 'ol', 'li', 'span', 'div',
        'figure', 'figcaption', 'iframe', 'table',
        'thead', 'tbody', 'tr', 'th', 'td'
    ]
    
    ALLOWED_HTML_ATTRIBUTES = {
        'a': ['href', 'title', 'target', 'rel', 'class'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'class', 'loading', 'decoding'],
        'div': ['class', 'id', 'data-theme'],
        'span': ['class'],
        'code': ['class'],
        'pre': ['class'],
        'iframe': ['src', 'width', 'height', 'frameborder', 
                 'allowfullscreen', 'allow', 'sandbox', 'loading', 'title'],
        'blockquote': ['class', 'cite'],
        'figure': ['class'],
        'figcaption': ['class'],
        'h1': ['id', 'class'], 'h2': ['id', 'class'], 'h3': ['id', 'class'], 
        'h4': ['id', 'class'], 'h5': ['id', 'class'], 'h6': ['id', 'class'],
        'table': ['class'], 'tr': ['class'], 'th': ['class', 'colspan', 'rowspan'],
        'td': ['class', 'colspan', 'rowspan']
    }
    
    # 외부 도메인 허용 목록 (보안 강화)
    ALLOWED_EXTERNAL_DOMAINS = {
        # 동영상/미디어
        'youtube.com', 'www.youtube.com', 'youtu.be',
        'vimeo.com', 'player.vimeo.com',
        
        # 기술/개발
        'github.com', 'raw.githubusercontent.com', 'gist.github.com',
        'stackoverflow.com', 'stackexchange.com',
        'codepen.io', 'jsfiddle.net',
        
        # 문서/참조
        'wikipedia.org', 'wikimedia.org',
        'developer.mozilla.org', 'docs.python.org',
        
        # 한국 서점/도서
        'kyobobook.co.kr', 'yes24.com', 'aladin.co.kr',
        'bookhouse.co.kr', 'ebook.kyobobook.co.kr',
        
        # 클라우드/CDN
        'cloudflare.com', 'jsdelivr.net', 'unpkg.com',
        
        # 이미지 호스팅
        'imgur.com', 'i.imgur.com',
        
        # 기타 신뢰할 수 있는 도메인
        'google.com', 'amazon.com', 'microsoft.com'
    }
    
    # 로깅 설정
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    
    # 프로덕션 환경에서는 stdout 로깅 권장
    if FLASK_ENV == 'production':
        LOG_TO_STDOUT = True
    
    # 애플리케이션 메타데이터
    APP_NAME = 'Flask Blog System'
    APP_VERSION = '2.0.0'
    APP_AUTHOR = '구센'
    APP_DESCRIPTION = '파일 시스템 기반 블로그 시스템'
    
    # 성능 설정
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1년 (정적 파일 캐싱)
    
    @staticmethod
    def init_app(app):
        """애플리케이션 초기화시 추가 설정"""
        # 프로덕션 환경 경고
        if app.config['FLASK_ENV'] == 'production':
            if app.config['SECRET_KEY'] == 'dev-only-secret-key-do-not-use-in-production':
                app.logger.critical("프로덕션 환경에서 개발용 SECRET_KEY를 사용하고 있습니다!")
            
            # HTTPS 사용 확인
            if not app.config.get('SESSION_COOKIE_SECURE'):
                app.logger.warning("프로덕션 환경에서 SESSION_COOKIE_SECURE가 활성화되지 않았습니다.")

class DevelopmentConfig(Config):
    """개발 환경 설정"""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    
    # 개발 환경에서는 세션 쿠키 보안 완화
    SESSION_COOKIE_SECURE = False
    
    # 개발 환경 로깅
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = False  # 개발시 파일 로깅도 유용
    
    # 캐시 타임아웃 단축 (빠른 변경 확인)
    CACHE_TIMEOUT = 60  # 1분

class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    FLASK_ENV = 'testing'
    
    # 테스트용 SECRET_KEY
    SECRET_KEY = 'test-secret-key-for-unit-tests'
    
    # 테스트 환경에서는 세션 쿠키 보안 비활성화
    SESSION_COOKIE_SECURE = False
    
    # 테스트용 디렉토리
    POSTS_DIR = str(basedir / 'tests' / 'test_posts')
    
    # 로깅 최소화
    LOG_LEVEL = 'ERROR'

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    
    # 프로덕션 전용 보안 강화
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_NAME = '__Host-session'  # __Host- 접두사로 추가 보안
    
    # 성능 최적화
    SEND_FILE_MAX_AGE_DEFAULT = 604800  # 1주일
    
    @classmethod
    def init_app(cls, app):
        """프로덕션 환경 초기화"""
        super().init_app(app)
        
        # 프로덕션 환경 검증
        import logging
        from logging.handlers import SysLogHandler
        
        # Syslog 핸들러 추가 (선택사항)
        if not cls.LOG_TO_STDOUT and sys.platform != 'win32':
            syslog_handler = SysLogHandler()
            syslog_handler.setLevel(logging.WARNING)
            app.logger.addHandler(syslog_handler)

# 설정 매핑
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig  # 기본값을 프로덕션으로 설정 (보안)
}