import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///blog.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # TinyMCE API 키 추가
    TINYMCE_API_KEY = os.environ.get('TIy5o6j48mfbmhiyaiseiohy6xz6sddyzobxl9dxz2j1hph95f', '기본_API_키')