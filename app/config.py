# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 기본 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-wagusen-2025')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # 보안 설정
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 경로 설정 - 모든 경로를 중앙화
    CONTENT_DIR = 'content'
    POSTS_DIR = os.path.join(CONTENT_DIR, 'posts')
    MEDIA_DIR = os.path.join(CONTENT_DIR, 'media')
    IMAGES_DIR = os.path.join(MEDIA_DIR, 'images')
    VIDEOS_DIR = os.path.join(MEDIA_DIR, 'videos')
    AUDIOS_DIR = os.path.join(MEDIA_DIR, 'audios')
    
    # 콘텐츠 설정
    POSTS_PER_PAGE = 6
    MAX_PREVIEW_LENGTH = 300
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # 캐싱 설정
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5분
    CACHE_THRESHOLD = 1000
    
    # 허용된 파일 확장자
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
        'video': {'mp4', 'webm', 'ogg', 'mov'},
        'audio': {'mp3', 'wav', 'flac', 'm4a', 'ogg'}
    }
    
    # 시뮬레이션 기본값
    SIMULATION_DEFAULTS = {
        'particle_count': 5,
        'gravity': 9.8,
        'friction': 0.01,
        'elasticity': 0.8
    }

class ProductionConfig(Config):
    DEBUG = False
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = 'cache'

class DevelopmentConfig(Config):
    DEBUG = True
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}