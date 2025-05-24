# app/utils.py - 깔끔한 경로 관리
from flask import current_app
import os

def get_content_path(subdir=None):
    """컨텐츠 경로 반환 유틸리티 함수"""
    content_folder = current_app.config.get('CONTENT_FOLDER', 
                                           os.path.join(current_app.root_path, 'static', 'content'))
    
    if subdir:
        return os.path.join(content_folder, subdir)
    return content_folder

def get_posts_dir():
    """텍스트 포스트 디렉토리 경로 반환"""
    return get_content_path('posts')

def get_media_dir():
    """미디어 파일 디렉토리 경로 반환"""
    return get_content_path('media')

def get_files_dir():
    """일반 파일 디렉토리 경로 반환"""
    return get_content_path('files')

def ensure_content_dirs():
    """필요한 컨텐츠 디렉토리들을 생성"""
    directories = [
        get_posts_dir(),    # 블로그 포스트
        get_media_dir(),    # 이미지, 비디오, 오디오
        get_files_dir()     # 기타 파일들
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    return directories

def is_safe_path(path, base_path):
    """경로가 기본 경로 내에 있는지 안전하게 확인"""
    if not isinstance(path, str) or not isinstance(base_path, str):
        return False
        
    try:
        # 절대 경로로 변환
        abs_path = os.path.abspath(path)
        abs_base = os.path.abspath(base_path)
        
        # base_path 내부에 있는지 확인
        return abs_path.startswith(abs_base)
    except Exception:
        return False

def get_file_extension(filename):
    """파일 확장자 반환"""
    if not isinstance(filename, str) or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()

def is_allowed_file_type(filename, allowed_extensions):
    """허용된 파일 형식인지 확인"""
    ext = get_file_extension(filename)
    return ext in allowed_extensions

# 허용된 파일 확장자 정의
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'ogg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}

def get_media_type(filename):
    """파일명으로부터 미디어 타입 판단"""
    ext = get_file_extension(filename)
    
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    elif ext in ALLOWED_AUDIO_EXTENSIONS:
        return 'audio'
    elif ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return 'document'
    else:
        return 'unknown'