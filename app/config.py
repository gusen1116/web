# app/config.py
import os
from datetime import timedelta
from typing import Dict, Set
from pathlib import Path

class Config:
    """애플리케이션 설정 - 단순화된 단일 설정 클래스"""
    
    # 기본 경로 설정
    BASE_DIR = Path(__file__).parent.absolute()
    
    # Flask 기본 설정
    DEBUG = False  # 항상 False로 고정
    TESTING = False
    
    # 보안 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wagusen-secret-key-2025-please-change-in-production'
    
    # CSRF 보호 설정
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1시간
    WTF_CSRF_SSL_STRICT = True if os.environ.get('HTTPS_ENABLED') else False
    
    # 세션 설정 - 보안 중심
    SESSION_COOKIE_SECURE = True if os.environ.get('HTTPS_ENABLED') else False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 24시간으로 단축
    
    # 콘텐츠 디렉토리 설정 (읽기 전용)
    CONTENT_DIR = BASE_DIR / 'content'
    POSTS_DIR = CONTENT_DIR / 'posts'
    
    # 캐싱 설정 - 성능 최적화 (읽기 전용이므로 긴 캐시 시간)
    CACHE_TIMEOUT = 600  # 10분
    POSTS_CACHE_SIZE = 1000  # 포스트 캐시 크기
    TAGS_CACHE_SIZE = 500   # 태그 캐시 크기
    
    # 정적 파일 캐싱 (1년)
    SEND_FILE_MAX_AGE_DEFAULT = 31536000
    
    # 콘텐츠 제한 설정 (읽기 전용 최적화)
    MAX_POSTS_PER_PAGE = 50  # 페이지당 최대 포스트 수
    MAX_POSTS_TOTAL = 2000   # 전체 최대 포스트 수
    MAX_TITLE_LENGTH = 200
    MAX_CONTENT_LENGTH = 2000000  # 2MB 텍스트 제한
    MAX_TAG_LENGTH = 50
    MAX_TAGS_PER_POST = 15
    MAX_PREVIEW_LENGTH = 300
    
    # 파일 시스템 설정 (읽기 전용)
    MAX_FILE_READ_SIZE = 10 * 1024 * 1024  # 읽을 수 있는 최대 파일 크기 10MB
    ALLOWED_TEXT_EXTENSIONS: Set[str] = {'txt', 'md'}  # 읽기 가능한 파일 확장자만
    
    # 보안 헤더 설정
    SECURITY_HEADERS: Dict[str, str] = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
    }
    
    # 로깅 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', False)
    
    # JSON 설정 - 성능 최적화
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    JSON_SORT_KEYS = False
    
    # 템플릿 설정 - 프로덕션 최적화
    TEMPLATES_AUTO_RELOAD = False
    EXPLAIN_TEMPLATE_LOADING = False
    
    # 마크다운 및 텍스트 처리 설정
    MARKDOWN_EXTENSIONS = [
        'extra', 'nl2br', 'sane_lists', 'codehilite', 'toc'
    ]
    
    # 콘텐츠 보안 설정
    ALLOWED_HTML_TAGS = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'hr', 'a', 'strong', 'em', 'b', 'i',
        'code', 'pre', 'blockquote', 'img',
        'ul', 'ol', 'li', 'span', 'div',
        'figure', 'figcaption', 'table', 'thead', 'tbody', 
        'tr', 'th', 'td', 'iframe'
    ]
    
    ALLOWED_HTML_ATTRIBUTES = {
        'a': ['href', 'title', 'target', 'rel', 'class'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'class', 'loading'],
        'div': ['class', 'id'],
        'span': ['class', 'id'],
        'code': ['class'],
        'pre': ['class'],
        'iframe': ['src', 'width', 'height', 'frameborder', 
                'allowfullscreen', 'allow', 'sandbox', 'loading'],
        'blockquote': ['class', 'cite'],
        'figure': ['class'],
        'figcaption': ['class'],
        'table': ['class'],
        'th': ['class', 'scope'],
        'td': ['class'],
        'h1': ['id'], 'h2': ['id'], 'h3': ['id'], 
        'h4': ['id'], 'h5': ['id'], 'h6': ['id']
    }
    
    # 외부 링크 도메인 허용 목록 (보안)
    ALLOWED_EXTERNAL_DOMAINS = {
        'youtube.com', 'youtu.be', 'vimeo.com',
        'github.com', 'gitlab.com', 'bitbucket.org',
        'stackoverflow.com', 'stackexchange.com',
        'wikipedia.org', 'wikimedia.org'
    }
    
    @classmethod
    def init_app(cls, app):
        """애플리케이션별 추가 설정"""
        # 필요한 디렉토리 생성
        cls.CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        cls.POSTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 환경 변수 기반 동적 설정
        if os.environ.get('HTTPS_ENABLED'):
            app.config['PREFERRED_URL_SCHEME'] = 'https'
            app.config['SESSION_COOKIE_SECURE'] = True
            app.config['WTF_CSRF_SSL_STRICT'] = True
        
        app.logger.info('설정 초기화 완료')

# 하위 호환성을 위한 별칭들
DevelopmentConfig = Config
ProductionConfig = Config  
TestingConfig = Config

# 설정 매핑 (기존 코드와의 호환성)
config = {
    'development': Config,
    'production': Config,
    'testing': Config,
    'default': Config
}