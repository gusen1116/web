# app/routes/posts_routes.py
from flask import Blueprint, render_template, send_from_directory, current_app, abort, url_for, request, redirect
import os
import re
from werkzeug.utils import secure_filename
from markupsafe import escape
from app.services.text_service import (
    get_all_text_posts, get_text_post, get_tags_count, 
    get_series_posts, get_adjacent_posts, render_content
)
from app.services.cache_service import CacheService

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

# 안전한 파일명 패턴 정의
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+\.(txt|jpg|jpeg|png|gif|webp|svg|mp4|webm|ogg|mov|mp3|wav|flac|m4a)$')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}

def validate_slug(slug):
    """슬러그 유효성 검증"""
    if not slug or not isinstance(slug, str):
        return False
    if len(slug) > 100:
        return False
    # 알파벳, 숫자, 하이픈, 언더스코어만 허용
    if not re.match(r'^[a-zA-Z0-9_\-]+$', slug):
        return False
    return True

def validate_tag(tag):
    """태그 유효성 검증"""
    if not tag or not isinstance(tag, str):
        return False
    if len(tag) > 50:
        return False
    # 기본 문자만 허용 (한글, 영문, 숫자, 공백, 하이픈)
    if not re.match(r'^[가-힣a-zA-Z0-9\s\-]+$', tag):
        return False
    return True

def validate_filename(filename):
    """파일명 유효성 검증"""
    if not filename or not isinstance(filename, str):
        return False
    if not SAFE_FILENAME_PATTERN.match(filename):
        return False
    # secure_filename으로 재검증
    if filename != secure_filename(filename):
        return False
    return True

@posts_bp.route('/')
def index():
    """텍스트 파일 목록 페이지"""
    try:
        # 캐시 서비스 사용
        posts = CacheService.get_posts_with_cache()
        tags_count = CacheService.get_tags_with_cache()
        
        # 태그 정렬 및 제한
        tags = [{"name": escape(tag), "count": count} 
                for tag, count in sorted(tags_count.items(), 
                key=lambda x: x[1], reverse=True)[:20]]
        
        # 최신 포스트 목록 (사이드바용)
        recent_posts = posts[:5] if len(posts) > 5 else posts
        
        return render_template(
            'posts/index.html', 
            posts=posts, 
            tags=tags,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f'포스트 목록 로드 오류: {str(e)}')
        abort(500)

@posts_bp.route('/<slug>')
def view_by_slug(slug):
    """슬러그로 포스트 찾기"""
    # 슬러그 검증
    if not validate_slug(slug):
        abort(400, "잘못된 요청입니다")
    
    posts_dir = current_app.config.get('POSTS_DIR')
    
    try:
        # 캐시된 포스트에서 찾기
        all_posts = CacheService.get_posts_with_cache()
        matching_post = None
        
        # 확장자가 있으면 제거
        slug_no_ext = os.path.splitext(slug)[0]
        
        for post in all_posts:
            if (hasattr(post, 'slug') and post.slug == slug) or \
               post.id == slug_no_ext or \
               post.filename == slug or \
               post.filename == slug + '.txt':
                matching_post = post
                break
        
        if not matching_post:
            abort(404, "포스트를 찾을 수 없습니다")
        
        # URL 생성
        base_url_images = url_for('posts.serve_image', filename='').rstrip('/')
        base_url_videos = url_for('posts.serve_video', filename='').rstrip('/')
        base_url_audios = url_for('posts.serve_audio', filename='').rstrip('/')
        
        # 컨텐츠 렌더링
        rendered_content = render_content(
            matching_post.content, 
            base_url_images, 
            base_url_videos, 
            base_url_audios
        )
        
        # 태그 정보
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": escape(tag), "count": count} 
                for tag, count in sorted(tags_count.items(), 
                key=lambda x: x[1], reverse=True)[:10]]
        
        # 이전/다음 포스트
        prev_post, next_post = get_adjacent_posts(posts_dir, matching_post)
        
        # 시리즈 정보
        series_posts = []
        if matching_post.series:
            series_posts = get_series_posts(posts_dir, matching_post.series)
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
    except Exception as e:
        current_app.logger.error(f'포스트 로드 오류: {str(e)}')
        abort(500)

@posts_bp.route('/view/<filename>')
def view_post(filename):
    """이전 URL 형식 지원 (리다이렉트)"""
    if not validate_filename(filename):
        abort(400, "잘못된 파일명입니다")
    return redirect(url_for('posts.view_by_slug', slug=filename))

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag):
    """태그별 텍스트 파일 필터링"""
    # 태그 검증
    if not validate_tag(tag):
        abort(400, "잘못된 태그입니다")
    
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        
        # 태그로 필터링된 포스트
        posts = get_all_text_posts(posts_dir, tag=tag)
        
        # 태그 카운트
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": escape(t), "count": count} 
                for t, count in sorted(tags_count.items(), 
                key=lambda x: x[1], reverse=True)[:20]]
        
        # 최신 포스트 목록
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        
        return render_template(
            'posts/index.html', 
            posts=posts, 
            tags=tags,
            recent_posts=recent_posts,
            current_tag=escape(tag)
        )
    except Exception as e:
        current_app.logger.error(f'태그 필터링 오류: {str(e)}')
        abort(500)

@posts_bp.route('/series/<series_name>')
def view_series(series_name):
    """시리즈의 모든 포스트 보기"""
    # 시리즈명 검증
    if not series_name or not isinstance(series_name, str) or len(series_name) > 100:
        abort(400, "잘못된 시리즈명입니다")
    
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        
        # 시리즈에 속한 포스트
        series_posts = get_series_posts(posts_dir, series_name)
        
        if not series_posts:
            abort(404, "시리즈를 찾을 수 없습니다")
        
        # 태그 카운트
        tags_count = CacheService.get_tags_with_cache()
        tags = [{"name": escape(tag), "count": count} 
                for tag, count in sorted(tags_count.items(), 
                key=lambda x: x[1], reverse=True)[:10]]
        
        # 최신 포스트 목록
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        
        return render_template(
            'posts/series.html', 
            series_name=escape(series_name),
            posts=series_posts,
            tags=tags,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f'시리즈 로드 오류: {str(e)}')
        abort(500)

def serve_static_file(filename, media_type):
    """정적 파일 서빙 헬퍼 함수"""
    # 파일명 검증
    if not validate_filename(filename):
        abort(403, "잘못된 파일명입니다")
    
    # 확장자 검증
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if media_type == 'image' and ext not in ALLOWED_IMAGE_EXTENSIONS:
        abort(403, "허용되지 않는 이미지 형식입니다")
    elif media_type == 'video' and ext not in ALLOWED_VIDEO_EXTENSIONS:
        abort(403, "허용되지 않는 비디오 형식입니다")
    elif media_type == 'audio' and ext not in ALLOWED_AUDIO_EXTENSIONS:
        abort(403, "허용되지 않는 오디오 형식입니다")
    
    # 미디어 디렉토리 경로
    media_dirs = {
        'image': 'img',
        'video': 'videos',
        'audio': 'audios'
    }
    
    media_dir = os.path.join(current_app.static_folder, media_dirs[media_type])
    
    # 경로 검증
    abs_path = os.path.abspath(os.path.join(media_dir, filename))
    if not abs_path.startswith(os.path.abspath(media_dir)):
        abort(403, "경로 위반입니다")
    
    # 파일 존재 확인
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        abort(404, f"{media_type} 파일을 찾을 수 없습니다")
    
    return send_from_directory(media_dir, filename)

@posts_bp.route('/images/<filename>')
def serve_image(filename):
    """이미지 파일 서빙"""
    return serve_static_file(filename, 'image')

@posts_bp.route('/videos/<filename>')
def serve_video(filename):
    """비디오 파일 서빙"""
    return serve_static_file(filename, 'video')

@posts_bp.route('/audios/<filename>')
def serve_audio(filename):
    """오디오 파일 서빙"""
    return serve_static_file(filename, 'audio')

# 에러 핸들러
@posts_bp.errorhandler(400)
def bad_request(error):
    return render_template('400.html', error=error), 400

@posts_bp.errorhandler(403)
def forbidden(error):
    return render_template('403.html', error=error), 403

@posts_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404

@posts_bp.errorhandler(500)
def internal_error(error):
    return render_template('500.html', error=error), 500