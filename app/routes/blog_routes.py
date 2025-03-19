# app/routes/blog_routes.py
from flask import Blueprint, render_template, request, jsonify, send_from_directory, url_for, redirect, abort, flash, current_app
from app import db
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.models.post_tag import PostTag
from werkzeug.utils import secure_filename
import os
import json
import time
from datetime import datetime
import uuid
from PIL import Image

# 블루프린트 정의 - 파일 상단에 위치
blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

# 파일 업로드 설정
UPLOAD_FOLDER = 'instance/uploads'
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz'},
    'audio': {'mp3', 'wav', 'ogg', 'flac'},
    'video': {'mp4', 'webm', 'avi', 'mov', 'mkv'}
}

def allowed_file(filename):
    """파일 확장자 확인"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return True, file_type
    return False, None

def get_file_type_icon(file_type):
    """파일 타입에 따른 아이콘 클래스 반환"""
    icons = {
        'image': 'fa-file-image',
        'document': 'fa-file-alt',
        'archive': 'fa-file-archive',
        'audio': 'fa-file-audio',
        'video': 'fa-file-video'
    }
    return icons.get(file_type, 'fa-file')

def optimize_image(file_path, max_width=1200, quality=85):
    """이미지 최적화 함수"""
    try:
        img = Image.open(file_path)
        
        # EXIF 정보에 따라 이미지 회전
        try:
            exif = img._getexif()
            if exif:
                orientation_key = 274  # EXIF 태그 번호 (Orientation)
                if orientation_key in exif:
                    orientation = exif[orientation_key]
                    
                    # 방향에 따라 이미지 회전
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
        except:
            pass
        
        # 이미지 크기 조정
        width, height = img.size
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # 이미지 저장 (원본 파일 교체)
        img.save(file_path, optimize=True, quality=quality)
        
        # 썸네일 생성 (원본 파일명_thumbnail.확장자)
        thumbnail_path = file_path.rsplit('.', 1)[0] + '_thumbnail.' + file_path.rsplit('.', 1)[1]
        thumbnail = img.copy()
        thumbnail.thumbnail((300, 300), Image.LANCZOS)
        thumbnail.save(thumbnail_path, optimize=True, quality=quality)
        
        return True
    except Exception as e:
        print(f"이미지 최적화 오류: {str(e)}")
        return False

def check_file_duplicate(file):
    """파일 중복 확인 (해시 기반)"""
    import hashlib
    
    # 파일 해시 계산
    md5_hash = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        md5_hash.update(chunk)
    file_hash = md5_hash.hexdigest()
    
    # 파일 포인터 위치 리셋
    file.seek(0)
    
    # 해시 값으로 중복 파일 검색
    try:
        from app.models.file import File
        existing_file = File.query.filter_by(file_hash=file_hash).first()
        return existing_file
    except:
        return None

# 블로그 목록
@blog_bp.route('/')
def index():
    """블로그 포스트 목록 페이지"""
    # 페이지네이션, 카테고리 필터, 태그 필터 처리
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 페이지당 게시물 수
    
    category_id = request.args.get('category', type=int)
    tag_id = request.args.get('tag', type=int)
    
    # 기본 쿼리 - 시간 역순
    query = Post.query.order_by(Post.created_at.desc())
    
    # 카테고리 필터 적용
    if category_id:
        query = query.filter(Post.category_id == category_id)
    
    # 태그 필터 적용
    if tag_id:
        query = query.join(Post.tags).filter(Tag.id == tag_id)
    
    # 페이지네이션 적용
    try:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        posts = pagination.items
    except:
        # Flask < 2.0 버전에서는 다른 방식으로 paginate 사용
        pagination = query.paginate(page, per_page, error_out=False)
        posts = pagination.items
    
    # 사이드바에 표시할 카테고리 목록
    categories = Category.query.all()
    
    # 사이드바에 표시할 태그 목록
    tags = Tag.query.all()
    
    # 사이드바에 표시할 최근 게시물
    current_post_ids = [post.id for post in posts]
    recent_posts = Post.query.filter(~Post.id.in_(current_post_ids if current_post_ids else [-1])).order_by(Post.created_at.desc()).limit(5).all()
    
    return render_template('blog/index.html', 
                        posts=posts, 
                        pagination=pagination,
                        tags=tags,
                        recent_posts=recent_posts)

# 검색 결과 페이지
@blog_bp.route('/search')
def search():
    """블로그 검색 결과"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('blog.index'))
    
    # 제목 또는 내용에서 검색
    search_term = f"%{query}%"
    posts = Post.query.filter(
        (Post.title.like(search_term)) | 
        (Post.content.like(search_term))
    ).order_by(Post.created_at.desc()).all()
    
    return render_template('blog/search.html', query=query, results=posts)

# 포스트 상세보기
@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    """블로그 포스트 상세 페이지"""
    post = Post.query.get_or_404(post_id)
    return render_template('blog/post.html', post=post)

# 파일 제공 라우트
@blog_bp.route('/uploads/<string:file_type>/<string:filename>')
def serve_file(file_type, filename):
    """업로드된 파일 제공"""
    # 애플리케이션 루트 기준의 절대 경로 사용
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    UPLOAD_FOLDER = os.path.join(basedir, 'instance', 'uploads')
    
    # 디렉토리가 존재하는지 확인하고 없으면 생성
    directory_path = os.path.join(UPLOAD_FOLDER, file_type)
    os.makedirs(directory_path, exist_ok=True)
    
    # 디버깅 출력
    full_path = os.path.join(directory_path, filename)
    print(f"요청된 파일 경로: {full_path}")
    print(f"파일 존재 여부: {os.path.exists(full_path)}")
    
    # 파일이 존재하지 않으면 디렉토리 내용 로깅 후 404 에러
    if not os.path.exists(full_path):
        # 디렉토리 내용 출력
        if os.path.exists(directory_path):
            print(f"디렉토리 내용: {os.listdir(directory_path)}")
        else:
            print(f"디렉토리가 존재하지 않음: {directory_path}")
        
        # 404 에러 반환
        return f"파일을 찾을 수 없습니다: {file_type}/{filename}", 404
    
    # 파일 전송
    return send_from_directory(directory_path, filename)

# 카테고리별 게시물 보기
@blog_bp.route('/category/<int:category_id>')
def category(category_id):
    """카테고리별 게시물 목록"""
    category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id).order_by(Post.created_at.desc()).all()
    return render_template('blog/category.html', category=category, posts=posts)

# 태그별 게시물 보기
@blog_bp.route('/tag/<int:tag_id>')
def tag(tag_id):
    """태그별 게시물 목록"""
    tag = Tag.query.get_or_404(tag_id)
    posts = Post.query.join(Post.tags).filter(Tag.id == tag_id).order_by(Post.created_at.desc()).all()
    return render_template('blog/tag.html', tag=tag, posts=posts)