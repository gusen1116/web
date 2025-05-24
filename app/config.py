# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-wagusen-2025'
    
    # 개발환경 설정
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # 보안 설정
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 제한