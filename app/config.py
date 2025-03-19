import os

class Config:
    SECRET_KEY = 'your-secret-key'
    
    # 데이터베이스 경로는 __init__.py에서 정의되므로 여기서는 제거
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 업로드 관련 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 최대 업로드 사이즈
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md'},
        'archive': {'zip', 'rar', '7z', 'tar', 'gz'},
        'audio': {'mp3', 'wav', 'ogg', 'flac'},
        'video': {'mp4', 'webm', 'avi', 'mov', 'mkv'}
    }