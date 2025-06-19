# app/routes/posts_routes.py (태그 기능 강화)
from flask import Blueprint, render_template, send_from_directory, current_app, abort, url_for, request, redirect, jsonify
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

# 미디어 타입별 허용 확장자 정의
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
    'video': {'mp4', 'webm', 'ogg', 'mov'},
    'audio': {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
}

# 안전한 파일명 패턴 (확장자 제외)
SAFE_FILENAME_BASE_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')

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

def validate_media_filename(filename, media_type):
    """
    미디어 파일명 유효성 검증 - 통합된 검증 로직
    
    Args:
        filename: 검증할 파일명
        media_type: 'image', 'video', 'audio' 중 하나
    
    Returns:
        bool: 유효한 파일명인지 여부
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # 파일명 길이 검사
    if len(filename) > 255:
        return False
    
    # secure_filename으로 재검증
    if filename != secure_filename(filename):
        return False
    
    # 경로 조작 시도 차단
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # 파일명과 확장자 분리
    if '.' not in filename:
        return False
    
    base_name, ext = filename.rsplit('.', 1)
    ext = ext.lower()
    
    # 기본 파일명 패턴 검증
    if not SAFE_FILENAME_BASE_PATTERN.match(base_name):
        return False
    
    # 미디어 타입별 확장자 검증
    if media_type not in ALLOWED_EXTENSIONS:
        return False
    
    if ext not in ALLOWED_EXTENSIONS[media_type]:
        return False
    
    return True

@posts_bp.route('/')
def index():
    """텍스트 파일 목록 페이지"""
    try:
        current_app.logger.info("포스트 인덱스 페이지 로드 시작")
        
        # 캐시 서비스 사용
        posts = CacheService.get_posts_with_cache()
        tags_count = CacheService.get_tags_with_cache()
        
        current_app.logger.info(f"로드된 포스트 수: {len(posts) if posts else 0}")
        current_app.logger.info(f"로드된 태그 수: {len(tags_count) if tags_count else 0}")
        
        # 태그 정렬 및 제한
        tags = []
        if tags_count:
            tags = [{"name": escape(tag), "count": count} 
                    for tag, count in sorted(tags_count.items(), 
                    key=lambda x: x[1], reverse=True)[:20]]
        
        # 최신 포스트 목록 (사이드바용)
        recent_posts = []
        if posts:
            recent_posts = posts[:5] if len(posts) > 5 else posts
        
        return render_template(
            'posts/index.html', 
            posts=posts or [], 
            tags=tags or [],
            recent_posts=recent_posts or []
        )
        
    except Exception as e:
        current_app.logger.error(f'포스트 목록 로드 오류: {str(e)}', exc_info=True)
        
        return render_template(
            'posts/index.html', 
            posts=[], 
            tags=[],
            recent_posts=[],
            error_message=f"포스트를 로드하는 중 오류가 발생했습니다: {str(e)}"
        )

@posts_bp.route('/tags')
def tags_overview():
    """태그 전체 보기 페이지"""
    try:
        tags_count = CacheService.get_tags_with_cache()
        
        # 태그를 알파벳/가나다 순으로 그룹화
        tag_groups = {}
        for tag, count in tags_count.items():
            first_char = tag[0].upper()
            if first_char not in tag_groups:
                tag_groups[first_char] = []
            tag_groups[first_char].append({
                'name': escape(tag),
                'count': count,
                'url': f'/posts/tag/{tag}'
            })
        
        # 각 그룹 내에서 정렬
        for char in tag_groups:
            tag_groups[char].sort(key=lambda x: x['name'])
        
        # 통계 정보
        total_tags = len(tags_count)
        total_usage = sum(tags_count.values())
        avg_usage = total_usage / total_tags if total_tags > 0 else 0
        
        # 인기 태그 TOP 10
        popular_tags = sorted(
            tags_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return render_template(
            'posts/tags_overview.html',
            tag_groups=sorted(tag_groups.items()),
            stats={
                'total_tags': total_tags,
                'total_usage': total_usage,
                'average_usage': round(avg_usage, 1)
            },
            popular_tags=[
                {'name': escape(tag), 'count': count}
                for tag, count in popular_tags
            ]
        )
    except Exception as e:
        current_app.logger.error(f'태그 개요 페이지 오류: {str(e)}')
        abort(500)

@posts_bp.route('/<slug>')
def view_by_slug(slug):
    """슬러그로 포스트 찾기 - 성능 최적화"""
    # 슬러그 검증
    if not validate_slug(slug):
        abort(400, "잘못된 요청입니다")
    
    posts_dir = current_app.config.get('POSTS_DIR')
    
    try:
        # 캐시된 포스트 인덱스 사용 (O(1) 조회)
        matching_post = CacheService.get_post_by_slug(slug)
        
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
    # 파일명 검증 (텍스트 파일용)
    if not filename or not isinstance(filename, str):
        abort(400, "잘못된 파일명입니다")
    
    # 텍스트 파일 검증
    allowed_text_extensions = current_app.config.get('ALLOWED_TEXT_EXTENSIONS', {'txt', 'md'})
    if not any(filename.endswith(f'.{ext}') for ext in allowed_text_extensions):
        # 확장자가 없으면 기본값 추가
        if '.' not in filename:
            filename = filename + '.txt'
    
    return redirect(url_for('posts.view_by_slug', slug=filename))

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag):
    """태그별 텍스트 파일 필터링 - 개선된 버전"""
    # 태그 검증
    if not validate_tag(tag):
        abort(400, "잘못된 태그입니다")
    
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        
        # 태그로 필터링된 포스트
        posts = get_all_text_posts(posts_dir, tag=tag)
        
        # 태그 카운트
        tags_count = CacheService.get_tags_with_cache()
        
        # 현재 태그와 함께 자주 사용되는 태그 찾기
        related_tags = []
        for post in posts:
            for other_tag in post.tags:
                if other_tag != tag:
                    related_tags.append(other_tag)
        
        # 관련 태그 빈도 계산
        related_tag_counts = {}
        for t in related_tags:
            related_tag_counts[t] = related_tag_counts.get(t, 0) + 1
        
        # 상위 5개 관련 태그
        top_related_tags = sorted(
            related_tag_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 전체 태그 목록 (사이드바용)
        all_tags = [{"name": escape(t), "count": count} 
                    for t, count in sorted(tags_count.items(), 
                    key=lambda x: x[1], reverse=True)[:20]]
        
        # 최신 포스트 목록
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        
        return render_template(
            'posts/tag.html',
            posts=posts, 
            current_tag=escape(tag),
            tag_count=tags_count.get(tag, 0),
            related_tags=[
                {"name": escape(t), "count": c} 
                for t, c in top_related_tags
            ],
            all_tags=all_tags,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f'태그 필터링 오류: {str(e)}')
        abort(500)

@posts_bp.route('/api/tags/autocomplete')
def tag_autocomplete():
    """태그 자동완성 API"""
    query = request.args.get('q', '').strip().lower()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        tags_count = CacheService.get_tags_with_cache()
        
        # 쿼리로 시작하는 태그 찾기
        matching_tags = [
            {
                'name': tag,
                'count': count,
                'url': f'/posts/tag/{tag}'
            }
            for tag, count in tags_count.items()
            if tag.lower().startswith(query)
        ]
        
        # 포함하는 태그도 찾기 (시작하는 것보다 후순위)
        containing_tags = [
            {
                'name': tag,
                'count': count,
                'url': f'/posts/tag/{tag}'
            }
            for tag, count in tags_count.items()
            if query in tag.lower() and not tag.lower().startswith(query)
        ]
        
        # 합치고 카운트순 정렬
        all_matches = matching_tags + containing_tags
        all_matches.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify(all_matches[:10])  # 최대 10개
        
    except Exception as e:
        current_app.logger.error(f'태그 자동완성 오류: {e}')
        return jsonify([])

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
    """정적 파일 서빙 헬퍼 함수 - 통합된 검증 로직 사용"""
    # 통합된 파일명 검증
    if not validate_media_filename(filename, media_type):
        current_app.logger.warning(f"잘못된 {media_type} 파일명 요청: {filename}")
        abort(403, f"잘못된 {media_type} 파일명입니다")
    
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
        current_app.logger.warning(f"경로 접근 위반 시도: {filename}")
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