# app/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'  # 환경변수 사용 권장
    
    # 불필요한 SQLALCHEMY_TRACK_MODIFICATIONS 제거
    
    # 업로드 관련 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 최대 업로드 사이즈
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md'},
        'archive': {'zip', 'rar', '7z', 'tar', 'gz'},
        'audio': {'mp3', 'wav', 'ogg', 'flac'},
        'video': {'mp4', 'webm', 'avi', 'mov', 'mkv'}
    }