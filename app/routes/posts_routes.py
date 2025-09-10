"""
app/routes/posts_routes.py
--------------------------

This module defines routes for serving and filtering blog posts stored as
text files. It includes validation helpers for slugs, tags, and media
filenames. Routes have been corrected to explicitly declare path
parameters instead of using a trailing space, which ensures that Flask
properly captures the variable parts of the URL. Error handling and
rendering remain consistent with the original code.
"""

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
from typing import Dict, List, Any

posts_bp = Blueprint('posts', __name__, url_prefix='/posts')

# Allowed media extensions per media type
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
    'video': {'mp4', 'webm', 'ogg', 'mov'},
    'audio': {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
}

# Safe filename base pattern (excluding extension)
SAFE_FILENAME_BASE_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')

def validate_slug(slug: str) -> bool:
    """Return True if ``slug`` is a valid post slug."""
    if not slug or not isinstance(slug, str) or len(slug) > 100:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', slug))

def validate_tag(tag: str) -> bool:
    """Return True if ``tag`` is a valid tag name."""
    if not tag or not isinstance(tag, str) or len(tag) > 50:
        return False
    return bool(re.match(r'^[가-힣a-zA-Z0-9\s\-]+$', tag))

def validate_media_filename(filename: str, media_type: str) -> bool:
    """Validate a media filename for images, videos, or audio files."""
    if not filename or not isinstance(filename, str):
        return False
    if len(filename) > 255:
        return False
    if filename != secure_filename(filename):
        return False
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    if '.' not in filename:
        return False
    base_name, ext = filename.rsplit('.', 1)
    ext = ext.lower()
    if not SAFE_FILENAME_BASE_PATTERN.match(base_name):
        return False
    if media_type not in ALLOWED_EXTENSIONS:
        return False
    return ext in ALLOWED_EXTENSIONS[media_type]

@posts_bp.route('/')
def index():
    """List all posts on the blog index page."""
    try:
        current_app.logger.info("포스트 인덱스 페이지 로드 시작")
        posts = CacheService.get_posts_with_cache()
        tags_count = CacheService.get_tags_with_cache()
        current_app.logger.info(f"로드된 포스트 수: {len(posts) if posts else 0}")
        current_app.logger.info(f"로드된 태그 수: {len(tags_count) if tags_count else 0}")
        tags = []
        if tags_count:
            tags = [
                {"name": escape(tag), "count": count}
                for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:20]
            ]
        recent_posts = posts[:5] if posts and len(posts) > 5 else posts or []
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
    """Display an overview of all tags grouped alphabetically."""
    try:
        tags_count = CacheService.get_tags_with_cache()
        tag_groups: Dict[str, List[Dict[str, Any]]] = {}
        for tag, count in tags_count.items():
            first_char = tag[0].upper()
            tag_groups.setdefault(first_char, []).append({
                'name': escape(tag),
                'count': count,
                'url': f'/posts/tag/{tag}'
            })
        # Sort each group
        for char in tag_groups:
            tag_groups[char].sort(key=lambda x: x['name'])
        total_tags = len(tags_count)
        total_usage = sum(tags_count.values())
        avg_usage = total_usage / total_tags if total_tags > 0 else 0
        popular_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        return render_template(
            'posts/tags_overview.html',
            tag_groups=sorted(tag_groups.items()),
            stats={
                'total_tags': total_tags,
                'total_usage': total_usage,
                'average_usage': round(avg_usage, 1)
            },
            popular_tags=[{'name': escape(tag), 'count': count} for tag, count in popular_tags]
        )
    except Exception as e:
        current_app.logger.error(f'태그 개요 페이지 오류: {str(e)}')
        abort(500)

@posts_bp.route('/<slug>')
def view_by_slug(slug: str):
    """Display a single post by its slug."""
    if not validate_slug(slug):
        abort(400, "잘못된 요청입니다")
    posts_dir = current_app.config.get('POSTS_DIR')
    try:
        matching_post = CacheService.get_post_by_slug_with_cache(slug)
        if not matching_post:
            abort(404, "포스트를 찾을 수 없습니다")
        base_url_images = url_for('posts.serve_image', filename='').rstrip('/')
        base_url_videos = url_for('posts.serve_video', filename='').rstrip('/')
        base_url_audios = url_for('posts.serve_audio', filename='').rstrip('/')
        rendered_content = render_content(
            matching_post.content,
            base_url_images,
            base_url_videos,
            base_url_audios
        )
        tags_count = CacheService.get_tags_with_cache()
        tags = [
            {"name": escape(tag), "count": count}
            for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        prev_post, next_post = get_adjacent_posts(posts_dir, matching_post)
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
def view_post(filename: str):
    """Support legacy URLs that include the filename with extension."""
    if not filename or not isinstance(filename, str):
        abort(400, "잘못된 파일명입니다")
    allowed_text_extensions = current_app.config.get('ALLOWED_TEXT_EXTENSIONS', {'txt', 'md'})
    if not any(filename.endswith(f'.{ext}') for ext in allowed_text_extensions):
        if '.' not in filename:
            filename = f'{filename}.txt'
    return redirect(url_for('posts.view_by_slug', slug=filename))

@posts_bp.route('/tag/<tag>')
def filter_by_tag(tag: str):
    """Filter posts by a specific tag."""
    if not validate_tag(tag):
        abort(400, "잘못된 태그입니다")
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        posts = get_all_text_posts(posts_dir, tag=tag)
        tags_count = CacheService.get_tags_with_cache()
        # Find related tags
        related_tags_list: List[str] = []
        for post in posts:
            for other_tag in post.tags:
                if other_tag != tag:
                    related_tags_list.append(other_tag)
        related_tag_counts: Dict[str, int] = {}
        for t in related_tags_list:
            related_tag_counts[t] = related_tag_counts.get(t, 0) + 1
        top_related_tags = sorted(related_tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        all_tags = [
            {"name": escape(t), "count": c}
            for t, c in sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:20]
        ]
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:5] if len(all_posts) > 5 else all_posts
        return render_template(
            'posts/tag.html',
            posts=posts,
            current_tag=escape(tag),
            tag_count=tags_count.get(tag, 0),
            related_tags=[{"name": escape(t), "count": c} for t, c in top_related_tags],
            all_tags=all_tags,
            recent_posts=recent_posts
        )
    except Exception as e:
        current_app.logger.error(f'태그 필터링 오류: {str(e)}')
        abort(500)

@posts_bp.route('/api/tags/autocomplete')
def tag_autocomplete():
    """Autocomplete API for tags. Returns up to 10 matching tags."""
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    try:
        tags_count = CacheService.get_tags_with_cache()
        matching_tags = [
            {'name': tag, 'count': count, 'url': f'/posts/tag/{tag}'}
            for tag, count in tags_count.items()
            if tag.lower().startswith(query)
        ]
        containing_tags = [
            {'name': tag, 'count': count, 'url': f'/posts/tag/{tag}'}
            for tag, count in tags_count.items()
            if query in tag.lower() and not tag.lower().startswith(query)
        ]
        all_matches = matching_tags + containing_tags
        all_matches.sort(key=lambda x: x['count'], reverse=True)
        return jsonify(all_matches[:10])
    except Exception as e:
        current_app.logger.error(f'태그 자동완성 오류: {e}')
        return jsonify([])

@posts_bp.route('/series/<series_name>')
def view_series(series_name: str):
    """Display all posts that belong to a series."""
    if not series_name or not isinstance(series_name, str) or len(series_name) > 100:
        abort(400, "잘못된 시리즈명입니다")
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        series_posts = get_series_posts(posts_dir, series_name)
        if not series_posts:
            abort(404, "시리즈를 찾을 수 없습니다")
        tags_count = CacheService.get_tags_with_cache()
        tags = [
            {"name": escape(tag), "count": count}
            for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
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

def serve_static_file(filename: str, media_type: str):
    """Helper for serving static media files after validation."""
    if not validate_media_filename(filename, media_type):
        current_app.logger.warning(f"잘못된 {media_type} 파일명 요청: {filename}")
        abort(403, f"잘못된 {media_type} 파일명입니다")
    media_dirs = {
        'image': 'images/posts',
        'video': 'videos',
        'audio': 'audios'
    }
    media_dir = os.path.join(current_app.static_folder, media_dirs[media_type])
    abs_path = os.path.abspath(os.path.join(media_dir, filename))
    if not abs_path.startswith(os.path.abspath(media_dir)):
        current_app.logger.warning(f"경로 접근 위반 시도: {filename}")
        abort(403, "경로 위반입니다")
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        abort(404, f"{media_type} 파일을 찾을 수 없습니다")
    return send_from_directory(media_dir, filename)

@posts_bp.route('/images/<filename>')
def serve_image(filename: str):
    """Serve an image file."""
    return serve_static_file(filename, 'image')

@posts_bp.route('/videos/<filename>')
def serve_video(filename: str):
    """Serve a video file."""
    return serve_static_file(filename, 'video')

@posts_bp.route('/audios/<filename>')
def serve_audio(filename: str):
    """Serve an audio file."""
    return serve_static_file(filename, 'audio')

# Blueprint-specific error handlers
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
