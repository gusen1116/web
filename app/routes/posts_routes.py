# app/routes/posts_routes.py
from flask import Blueprint, render_template, send_from_directory, current_app, abort, url_for, request, redirect
import os
import sys
from app.services.text_service import (
    TextPost, parse_text_file, render_content, get_all_text_posts,
    get_text_post, get_tags_count, find_related_posts, search_posts
)

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

@posts_bp.route('/')
def index():
    """텍스트 파일 목록 페이지"""
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 디렉토리가 없으면 생성
    os.makedirs(text_dir, exist_ok=True)
    
    # 모든 텍스트 파일 가져오기
    posts = get_all_text_posts(text_dir)
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 최신 포스트 목록 (사이드바용)
    recent_posts = posts[:5] if len(posts) > 5 else posts
    
    return render_template(
        'posts/index.html', 
        posts=posts, 
        tags=tags,
        recent_posts=recent_posts
    )

@posts_bp.route('/<filename>')
def view_post(filename):
    """텍스트 파일 내용 보기"""
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 텍스트 파일 가져오기
    post = get_text_post(text_dir, filename)
    
    if not post:
        abort(404)
    
    # 렌더링된 HTML 생성
    base_url_images = url_for('posts.serve_image', filename='').rstrip('/')
    base_url_files = url_for('posts.serve_file', filename='').rstrip('/')
    rendered_content = render_content(post.content, base_url_images, base_url_files)
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 관련 포스트 가져오기
    related_posts = find_related_posts(text_dir, post, limit=3)
    
    return render_template(
        'posts/view.html', 
        post=post, 
        rendered_content=rendered_content,
        tags=tags, 
        related_posts=related_posts
    )

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag):
    """태그별 텍스트 파일 필터링"""
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 태그로 필터링된 포스트 가져오기
    posts = get_all_text_posts(text_dir, tag=tag)
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": t, "count": count} for t, count in tags_count.items()]
    
    # 최신 포스트 목록 (사이드바용)
    all_posts = get_all_text_posts(text_dir)
    recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
    
    return render_template(
        'posts/index.html', 
        posts=posts, 
        tags=tags,
        recent_posts=recent_posts,
        current_tag=tag
    )

@posts_bp.route('/search')
def search():
    """포스트 검색"""
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('posts.index'))
    
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 검색 결과 가져오기
    posts = search_posts(text_dir, query)
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 최신 포스트 목록 (사이드바용)
    all_posts = get_all_text_posts(text_dir)
    recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
    
    return render_template(
        'posts/search.html', 
        posts=posts, 
        tags=tags,
        recent_posts=recent_posts,
        query=query
    )

@posts_bp.route('/images/<filename>')
def serve_image(filename):
    """이미지 파일 서빙"""
    images_dir = os.path.join(current_app.instance_path, 'uploads', 'images')
    return send_from_directory(images_dir, filename)

@posts_bp.route('/files/<filename>')
def serve_file(filename):
    """파일 다운로드"""
    files_dir = os.path.join(current_app.instance_path, 'uploads', 'files')
    return send_from_directory(files_dir, filename, as_attachment=True)

@posts_bp.route('/debug')
def debug_paths():
    """경로 디버깅"""
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    debug_info = {
        'text_dir': text_dir,
        'text_dir_exists': os.path.exists(text_dir),
        'text_files': os.listdir(text_dir) if os.path.exists(text_dir) else [],
        'instance_path': current_app.instance_path,
        'uploads_dir': os.path.join(current_app.instance_path, 'uploads'),
        'uploads_dir_exists': os.path.exists(os.path.join(current_app.instance_path, 'uploads')),
    }
    
    return render_template('posts/debug.html', debug_info=debug_info)