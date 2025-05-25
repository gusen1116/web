# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-wagusen-2025'
    
    # 개발환경 설정
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # 보안 설정
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # 콘텐츠 디렉토리 설정
    CONTENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content')
    POSTS_DIR = os.path.join(CONTENT_DIR, 'posts')
    
    # 캐싱 설정
    CACHE_TIMEOUT = 300  # 5분
    
    # 프로덕션 설정
    SEND_FILE_MAX_AGE_DEFAULT = 0 if DEBUG else 31536000  # 개발: 0, 프로덕션: 1년

class ProductionConfig(Config):
    DEBUG = False
    # 프로덕션 전용 설정
    PREFERRED_URL_SCHEME = 'https'