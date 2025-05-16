# app/routes/posts_routes.py
from flask import Blueprint, render_template, send_from_directory, current_app, abort, url_for, request, redirect
import os
import sys
from werkzeug.utils import secure_filename
from markupsafe import escape
from app.services.text_service import (
    TextPost, parse_text_file, render_content, get_all_text_posts,
    get_text_post, get_tags_count, find_related_posts, search_posts,
    get_series_posts, get_adjacent_posts
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

@posts_bp.route('/<slug>')
def view_by_slug(slug):
    """슬러그, ID 또는 파일명으로 포스트 찾기"""
    # 안전한 슬러그 검증
    if not isinstance(slug, str) or len(slug) > 100:
        abort(400, "잘못된 요청입니다")
    
    # XSS 방지를 위한 이스케이핑
    slug = escape(slug)
    
    # 파일 경로 조작 문자 검사
    if '..' in slug or '/' in slug or '\\' in slug:
        abort(400, "잘못된 슬러그 형식입니다")
    
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 모든 텍스트 파일을 로드
    all_posts = get_all_text_posts(text_dir)
    matching_post = None
    
    # 확장자가 있으면 제거
    slug_no_ext = os.path.splitext(slug)[0]
    
    for post in all_posts:
        # 슬러그가 있는 경우 먼저 확인
        if hasattr(post, 'slug') and post.slug and post.slug == slug:
            matching_post = post
            break
        # ID로 확인
        elif post.id == slug_no_ext:
            matching_post = post
            break
        # 파일명으로 확인
        elif post.filename == slug or post.filename == slug + '.txt':
            matching_post = post
            break
    
    if not matching_post:
        abort(404, "포스트를 찾을 수 없습니다")
    
    # 이후 렌더링 로직
    base_url_images = url_for('posts.serve_image', filename='').rstrip('/')
    base_url_files = url_for('posts.serve_file', filename='').rstrip('/')
    rendered_content = render_content(matching_post.content, base_url_images, base_url_files)
    
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 디버깅 정보 추가 - 운영 환경에서는 로깅 안함
    if current_app.debug:
        current_app.logger.debug(f"현재 포스트: {matching_post.id}, {matching_post.filename}")
        
        # 이전/다음 포스트 가져오기
        prev_post, next_post = get_adjacent_posts(text_dir, matching_post)
        
        # 이전/다음 포스트 디버깅 정보
        if prev_post:
            current_app.logger.debug(f"이전 포스트: {prev_post.id}, {prev_post.title}")
        if next_post:
            current_app.logger.debug(f"다음 포스트: {next_post.id}, {next_post.title}")
    else:
        # 운영 환경에서는 로깅 없이 포스트만 가져옴
        prev_post, next_post = get_adjacent_posts(text_dir, matching_post)
    
    # 시리즈 정보가 있을 경우 시리즈의 다른 포스트 가져오기
    series_posts = []
    if matching_post.series:
        series_posts = get_series_posts(text_dir, matching_post.series)
        # 현재 포스트 제외
        series_posts = [p for p in series_posts if p.filename != matching_post.filename]
    
    return render_template(
        'posts/view.html', 
        post=matching_post, 
        rendered_content=rendered_content,
        tags=tags,
        prev_post=prev_post,
        next_post=next_post,
        series_posts=series_posts
    )

@posts_bp.route('/view/<filename>')
def view_post(filename):
    """이전 URL 형식 지원"""
    # 파일명 검증
    if not is_safe_filename(filename):
        abort(400, "잘못된 파일명입니다")
        
    return redirect(url_for('posts.view_by_slug', slug=filename))

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag):
    """태그별 텍스트 파일 필터링"""
    # 태그 검증
    if not isinstance(tag, str) or len(tag) > 50:
        abort(400, "잘못된 태그 요청입니다")
    
    # XSS 방지를 위한 이스케이핑
    tag = escape(tag)
    
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

@posts_bp.route('/series/<series_name>')
def view_series(series_name):
    """시리즈의 모든 포스트 보기"""
    # 시리즈명 검증
    if not isinstance(series_name, str) or len(series_name) > 100:
        abort(400, "잘못된 시리즈명입니다")
    
    # XSS 방지를 위한 이스케이핑
    series_name = escape(series_name)
    
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 시리즈에 속한 모든 포스트 가져오기
    series_posts = get_series_posts(text_dir, series_name)
    
    if not series_posts:
        abort(404, "시리즈를 찾을 수 없습니다")
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 최신 포스트 목록 (사이드바용)
    all_posts = get_all_text_posts(text_dir)
    recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
    
    return render_template(
        'posts/series.html', 
        series_name=series_name,
        posts=series_posts,
        tags=tags,
        recent_posts=recent_posts
    )

@posts_bp.route('/images/<filename>')
def serve_image(filename):
    """이미지 파일 서빙 - 보안 강화"""
    # 파일명 검증
    if not is_safe_filename(filename):
        abort(403, "잘못된 파일명입니다")
    
    # 확장자 검증
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        abort(403, "허용되지 않는 파일 형식입니다")
    
    images_dir = os.path.join(current_app.instance_path, 'uploads', 'images')
    
    # 경로 검증
    abs_path = os.path.abspath(os.path.join(images_dir, filename))
    if not abs_path.startswith(os.path.abspath(images_dir)):
        abort(403, "경로 위반입니다")
    
    # 파일 존재 확인
    if not os.path.exists(abs_path):
        abort(404, "이미지를 찾을 수 없습니다")
    
    # 파일 크기 제한 (선택적)
    if os.path.getsize(abs_path) > 10 * 1024 * 1024:  # 10MB 제한
        abort(403, "파일 크기가 너무 큽니다")
    
    return send_from_directory(images_dir, filename)

@posts_bp.route('/files/<filename>')
def serve_file(filename):
    """파일 다운로드 - 보안 강화"""
    # 파일명 검증
    if not is_safe_filename(filename):
        abort(403, "잘못된 파일명입니다")
    
    # 확장자 검증
    allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'md', 'zip', 'rar', '7z'}
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        abort(403, "허용되지 않는 파일 형식입니다")
    
    files_dir = os.path.join(current_app.instance_path, 'uploads', 'files')
    
    # 경로 검증
    abs_path = os.path.abspath(os.path.join(files_dir, filename))
    if not abs_path.startswith(os.path.abspath(files_dir)):
        abort(403, "경로 위반입니다")
    
    # 파일 존재 확인
    if not os.path.exists(abs_path):
        abort(404, "파일을 찾을 수 없습니다")
    
    # 파일 크기 제한 (선택적)
    if os.path.getsize(abs_path) > 50 * 1024 * 1024:  # 50MB 제한
        abort(403, "파일 크기가 너무 큽니다")
    
    return send_from_directory(files_dir, filename, as_attachment=True)

@posts_bp.route('/search')
def search():
    """포스트 검색 기능"""
    query = request.args.get('q', '')
    
    # 검색어 검증
    if not isinstance(query, str) or len(query) > 100:
        abort(400, "잘못된 검색 요청입니다")
    
    # 검색어 이스케이핑
    query = escape(query)
    
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 검색 결과 가져오기
    results = search_posts(text_dir, query) if query else []
    
    # 태그 카운트 가져오기
    tags_count = get_tags_count(text_dir)
    tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
    
    # 최신 포스트 목록 (사이드바용)
    all_posts = get_all_text_posts(text_dir)
    recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
    
    return render_template(
        'posts/search.html',
        query=query,
        posts=results,
        tags=tags,
        recent_posts=recent_posts
    )

@posts_bp.route('/debug')
def debug_paths():
    """경로 디버깅 - 운영 환경에서 비활성화 필요"""
    # 운영 환경에서는 이 기능 비활성화
    if not current_app.debug:
        abort(403, "디버그 모드에서만 사용 가능합니다")
    
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    debug_info = {
        'text_dir': text_dir,
        'text_dir_exists': os.path.exists(text_dir),
        'text_files': os.listdir(text_dir) if os.path.exists(text_dir) else [],
        'instance_path': current_app.instance_path,
        'uploads_dir': os.path.join(current_app.instance_path, 'uploads'),
        'uploads_dir_exists': os.path.exists(os.path.join(current_app.instance_path, 'uploads')),
        'server_info': {
            'python_version': sys.version,
            'timezone': os.environ.get('TZ', 'Not set')
        }
    }
    
    return render_template('posts/debug.html', debug_info=debug_info)

# 보안 강화 유틸리티 함수
def is_safe_filename(filename):
    """안전한 파일명인지 확인"""
    # 기본 검증
    if not isinstance(filename, str) or not filename:
        return False
    
    # 경로 탐색 패턴 검사
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # 숨김 파일 검사
    if filename.startswith('.'):
        return False
    
    # 파일명 길이 제한
    if len(filename) > 255:
        return False
    
    # 특수 문자 검사
    if not all(c.isprintable() for c in filename):
        return False
    
    # Werkzeug의 secure_filename 검증
    return filename == secure_filename(filename)