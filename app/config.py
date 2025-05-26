# app/config.py
import os
from datetime import timedelta

class Config:
    """기본 설정"""
    
    # 보안 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-wagusen-2025-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = True
    
    # 세션 설정
    SESSION_COOKIE_SECURE = False  # HTTPS에서는 True로 설정
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    
    # 개발환경 설정
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    TESTING = False
    
    # 콘텐츠 디렉토리 설정
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONTENT_DIR = os.path.join(BASE_DIR, 'content')
    POSTS_DIR = os.path.join(CONTENT_DIR, 'posts')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'instance', 'uploads')
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx',
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg',
        'mp4', 'webm', 'ogg', 'mov',
        'mp3', 'wav', 'flac', 'm4a'
    }
    
    # 캐싱 설정
    CACHE_TIMEOUT = 300  # 5분
    SEND_FILE_MAX_AGE_DEFAULT = 0 if DEBUG else 31536000  # 개발: 0, 프로덕션: 1년
    
    # 로깅 설정
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # 보안 헤더 설정
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # 레이트 리미팅 설정
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # JSON 설정
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # 템플릿 설정
    TEMPLATES_AUTO_RELOAD = DEBUG
    EXPLAIN_TEMPLATE_LOADING = False
    
    # 정적 파일 설정
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # 개발 환경에서는 보안 쿠키 비활성화
    SESSION_COOKIE_SECURE = False
    
    # 개발 환경 로깅
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    TESTING = False
    
    # 프로덕션 보안 설정
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'
    
    # 정적 파일 캐싱
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1년
    
    # 프로덕션 로깅
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
    # 프로덕션 데이터베이스 설정 (필요시)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    @property
    def SECRET_KEY(self):
        """프로덕션에서는 환경 변수에서 시크릿 키 필수"""
        secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("프로덕션 환경에서는 SECRET_KEY 환경 변수가 필요합니다!")
        return secret_key


class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    DEBUG = True
    
    # 테스트용 시크릿 키
    SECRET_KEY = 'test-secret-key'
    
    # CSRF 비활성화 (테스트 편의성)
    WTF_CSRF_ENABLED = False
    
    # 테스트 데이터베이스
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}