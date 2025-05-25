# app/routes/posts_routes.py
from flask import Blueprint, render_template, send_from_directory, current_app, abort, url_for, request
import os
from markupsafe import escape
from app.services.cache_service import CacheService
from app.services.content_service import ContentService
from app.services.file_service import FileService

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

@posts_bp.route('/')
def index():
    """포스트 목록 페이지"""
    try:
        posts = CacheService.get_posts_with_cache()
        tags_count = CacheService.get_tags_with_cache()
        
        # 태그를 딕셔너리 형태로 변환
        tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
        
        # 최신 포스트 (사이드바용)
        recent_posts = posts[:5] if len(posts) > 5 else posts
        
        return render_template(
            'posts/index.html',
            posts=posts,
            tags=tags,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f'포스트 목록 로드 에러: {str(e)}')
        return render_template('posts/index.html', posts=[], tags=[], recent_posts=[])

@posts_bp.route('/<slug>')
def view_by_slug(slug):
    """슬러그로 포스트 보기"""
    # 입력 검증
    if not isinstance(slug, str) or len(slug) > 100:
        abort(400)
    
    slug = escape(slug)
    
    # 위험한 문자 검사
    if any(char in slug for char in ['..', '/', '\\']):
        abort(400)
    
    # 캐시에서 포스트 찾기
    post = CacheService.get_post_with_cache(slug)
    if not post:
        abort(404)
    
    try:
        # 렌더링된 콘텐츠 가져오기
        rendered_content = CacheService.get_rendered_content_with_cache(post)
        
        # 태그 정보
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
        
        # 이전/다음 포스트
        prev_post, next_post = FileService.get_adjacent_posts(post)
        
        # 시리즈 포스트
        series_posts = []
        if post.series:
            series_posts = FileService.get_series_posts(post.series)
            series_posts = [p for p in series_posts if p.id != post.id]
        
        return render_template(
            'posts/view.html',
            post=post,
            rendered_content=rendered_content,
            tags=tags,
            prev_post=prev_post,
            next_post=next_post,
            series_posts=series_posts
        )
        
    except Exception as e:
        current_app.logger.error(f'포스트 렌더링 에러 {slug}: {str(e)}')
        abort(500)

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag):
    """태그별 포스트 필터링"""
    if not isinstance(tag, str) or len(tag) > 50:
        abort(400)
    
    tag = escape(tag)
    
    try:
        # 태그별 포스트 가져오기
        all_posts = CacheService.get_posts_with_cache()
        posts = [post for post in all_posts if tag in post.tags]
        
        # 태그 정보
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": t, "count": count} for t, count in tags_count.items()]
        
        # 최신 포스트 (사이드바용)
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        
        return render_template(
            'posts/index.html',
            posts=posts,
            tags=tags,
            recent_posts=recent_posts,
            current_tag=tag
        )
        
    except Exception as e:
        current_app.logger.error(f'태그 필터링 에러 {tag}: {str(e)}')
        abort(500)

@posts_bp.route('/series/<series_name>')
def view_series(series_name):
    """시리즈별 포스트 보기"""
    if not isinstance(series_name, str) or len(series_name) > 100:
        abort(400)
    
    series_name = escape(series_name)
    
    try:
        series_posts = FileService.get_series_posts(series_name)
        
        if not series_posts:
            abort(404)
        
        # 태그 정보
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": tag, "count": count} for tag, count in tags_count.items()]
        
        # 최신 포스트 (사이드바용)
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        
        return render_template(
            'posts/series.html',
            series_name=series_name,
            posts=series_posts,
            tags=tags,
            recent_posts=recent_posts
        )
        
    except Exception as e:
        current_app.logger.error(f'시리즈 로드 에러 {series_name}: {str(e)}')
        abort(500)

# 미디어 파일 서빙 (개발환경용)
@posts_bp.route('/images/<filename>')
def serve_image(filename):
    """이미지 파일 서빙 (개발용)"""
    if not current_app.debug:
        abort(404)  # 프로덕션에서는 nginx가 처리
    
    return _serve_media_file(filename, 'images', current_app.config['ALLOWED_EXTENSIONS']['image'])

@posts_bp.route('/videos/<filename>')
def serve_video(filename):
    """비디오 파일 서빙 (개발용)"""
    if not current_app.debug:
        abort(404)
    
    return _serve_media_file(filename, 'videos', current_app.config['ALLOWED_EXTENSIONS']['video'])

@posts_bp.route('/audios/<filename>')
def serve_audio(filename):
    """오디오 파일 서빙 (개발용)"""
    if not current_app.debug:
        abort(404)
    
    return _serve_media_file(filename, 'audios', current_app.config['ALLOWED_EXTENSIONS']['audio'])

def _serve_media_file(filename, media_type, allowed_extensions):
    """미디어 파일 서빙 헬퍼"""
    # 파일명 검증
    if not isinstance(filename, str) or not filename:
        abort(403)
    
    if any(char in filename for char in ['..', '/', '\\']):
        abort(403)
    
    # 확장자 검증
    if '.' not in filename:
        abort(403)
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        abort(403)
    
    # 파일 경로
    media_dir = getattr(current_app.config, f'{media_type.upper()}_DIR')
    file_path = os.path.join(media_dir, filename)
    
    # 경로 안전성 검증
    abs_path = os.path.abspath(file_path)
    abs_base = os.path.abspath(media_dir)
    
    if not abs_path.startswith(abs_base):
        abort(403)
    
    if not os.path.exists(abs_path):
        abort(404)
    
    return send_from_directory(media_dir, filename)