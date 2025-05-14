# app/utils.py 생성
from flask import current_app
import os

def get_upload_path(subdir=None):
    """업로드 경로 반환 유틸리티 함수"""
    if subdir:
        return os.path.join(current_app.instance_path, 'uploads', subdir)
    return os.path.join(current_app.instance_path, 'uploads')

def get_text_dir():
    """텍스트 파일 디렉토리 경로 반환"""
    return get_upload_path('texts')

def get_image_dir():
    """이미지 파일 디렉토리 경로 반환"""
    return get_upload_path('images')

def get_file_dir():
    """일반 파일 디렉토리 경로 반환"""
    return get_upload_path('files')