"""
app/routes/main_routes.py
-------------------------

This module defines the routes for the main pages of the application, such
as the index, about, tag APIs, and sitemap generation. Several issues from
the original code have been fixed:

* The related tags API now declares the ``tag`` parameter in the route
  definition, allowing Flask to capture it properly.
* The sitemap generator now emits valid XML instead of placeholder spaces.
* Comments and type annotations have been added for clarity.
"""

from flask import Blueprint, render_template, current_app, jsonify, request, Response, url_for
from typing import List, Dict, Any
from datetime import datetime
from app.services.text_service import TextPost, get_all_text_posts, get_tags_count
from app.services.color_service import ColorService
import os

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the home page with all posts, recent posts, and popular tags."""
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        all_posts = get_all_text_posts(posts_dir)
        recent_posts = all_posts[:3] if all_posts else []
        popular_tags = _get_popular_tags(limit=10)
        return render_template(
            'index.html',
            posts=all_posts,
            recent_posts=recent_posts,
            popular_tags=popular_tags
        )
    except Exception as e:
        current_app.logger.error(f'메인 페이지 로드 에러: {e}')
        return render_template(
            'index.html',
            posts=[],
            recent_posts=[],
            popular_tags=[],
            error_message="일시적으로 콘텐츠를 불러올 수 없습니다."
        )

@main_bp.route('/about')
def about():
    """Render a simple about page."""
    try:
        return render_template('about.html')
    except Exception as e:
        current_app.logger.error(f'소개 페이지 로드 에러: {e}')
        return render_template('404.html'), 500

@main_bp.route('/test')
def test():
    return render_template('test.html')

@main_bp.route('/magazine')
def magazine():
    page = request.args.get('page', 1, type=int)
    PER_PAGE = 9
    posts_dir = current_app.config.get('POSTS_DIR')
    all_posts = get_all_text_posts(posts_dir)
    total_posts = len(all_posts)
    total_pages = (total_posts + PER_PAGE - 1) // PER_PAGE

    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_posts = all_posts[start:end]

    posts_with_colors = []
    for post in paginated_posts:
        preview = post.get_rich_preview(100)
        image_path = None
        if preview['image_filename']:
            image_path = os.path.join(current_app.static_folder, 'images/posts', preview['image_filename'])
        
        dominant_color = ColorService.get_dominant_color(image_path) if image_path else '#FFFFFF'
        posts_with_colors.append({
            'post': post,
            'color': dominant_color
        })

    return render_template(
        'magazine.html', 
        posts_with_colors=posts_with_colors,
        current_page=page,
        total_pages=total_pages
    )

@main_bp.route('/api/status')
def api_status():
    """Return basic status information about the application."""
    try:
        status_info: Dict[str, Any] = {
            'status': 'healthy',
            'version': '2.0.0',
            'environment': current_app.config.get('FLASK_ENV', 'production'),
        }
        # Add content statistics
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            all_posts = get_all_text_posts(posts_dir)
            tags_count = get_tags_count(posts_dir)
            status_info['content'] = {
                'total_posts': len(all_posts),
                'total_tags': len(tags_count),
                'latest_post_date': all_posts[0].date.isoformat() if all_posts else None
            }
        except Exception as content_error:
            current_app.logger.warning(f'콘텐츠 통계 수집 실패: {content_error}')
            status_info['content'] = {'status': 'unavailable'}
        return jsonify(status_info)
    except Exception as e:
        current_app.logger.error(f'상태 API 오류: {e}')
        return jsonify({'status': 'error', 'message': '시스템 상태를 확인할 수 없습니다'}), 500

@main_bp.route('/api/tags')
def api_tags():
    """Return a tag cloud along with some statistics."""
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        tags_count = get_tags_count(posts_dir)
        sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)
        max_count = sorted_tags[0][1] if sorted_tags else 1
        min_count = sorted_tags[-1][1] if sorted_tags else 1
        tag_cloud: List[Dict[str, Any]] = []
        for tag, count in sorted_tags:
            # Compute size from 1 to 5 based on relative frequency
            if max_count == min_count:
                size = 3
            else:
                size = int(1 + (count - min_count) * 4 / (max_count - min_count))
            tag_cloud.append({
                'name': tag,
                'count': count,
                'size': size,
                'url': f'/posts/tag/{tag}'
            })
        return jsonify({
            'tags': tag_cloud,
            'total': len(tag_cloud),
            'stats': {
                'most_used': sorted_tags[0] if sorted_tags else None,
                'least_used': sorted_tags[-1] if sorted_tags else None,
                'average_count': sum(count for _, count in sorted_tags) / len(sorted_tags) if sorted_tags else 0
            }
        })
    except Exception as e:
        current_app.logger.error(f'태그 API 오류: {e}')
        return jsonify({'error': '태그 정보를 가져올 수 없습니다'}), 500

@main_bp.route('/api/related-tags/<tag>')
def api_related_tags(tag: str):
    """Find tags that are frequently used together with the given tag."""
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        all_posts = get_all_text_posts(posts_dir)
        posts_with_tag = [p for p in all_posts if tag in p.tags]
        if not posts_with_tag:
            return jsonify({'related_tags': []})
        related_tags: Dict[str, int] = {}
        for post in posts_with_tag:
            for other_tag in post.tags:
                if other_tag != tag:
                    related_tags[other_tag] = related_tags.get(other_tag, 0) + 1
        sorted_related = sorted(related_tags.items(), key=lambda x: x[1], reverse=True)[:10]
        return jsonify({
            'tag': tag,
            'related_tags': [
                {'name': t, 'count': c, 'url': f'/posts/tag/{t}'}
                for t, c in sorted_related
            ]
        })
    except Exception as e:
        current_app.logger.error(f'관련 태그 API 오류: {e}')
        return jsonify({'error': '관련 태그를 가져올 수 없습니다'}), 500

def _get_popular_tags(limit: int = 10) -> List[Dict[str, Any]]:
    """Return a list of the most popular tags limited by ``limit``."""
    try:
        posts_dir = current_app.config.get('POSTS_DIR')
        tags_count = get_tags_count(posts_dir)
        sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        result: List[Dict[str, Any]] = []
        for tag, count in sorted_tags:
            result.append({'name': tag, 'count': count, 'url': f'/posts/tag/{tag}'})
        return result
    except Exception as e:
        current_app.logger.error(f'인기 태그 처리 오류: {e}')
        return []

@main_bp.route('/robots.txt')
def robots_txt() -> Response:
    """Serve a simple robots.txt."""
    robots_content = """
User-agent: *
Allow: /
Allow: /posts/
Allow: /about
Allow: /simulation/

Disallow: /api/
Disallow: /admin/
Disallow: /logs/

Sitemap: /sitemap.xml
"""
    return Response(robots_content.strip(), mimetype='text/plain')

@main_bp.route('/sitemap.xml')
def sitemap_xml() -> Response:
    """Generate and return a sitemap XML with URLs from the site."""
    try:
        # Base pages
        urls: List[Dict[str, str]] = [
            {
                'loc': url_for('main.index', _external=True),
                'lastmod': datetime.now().strftime('%Y-%m-%d'),
                'changefreq': 'daily',
                'priority': '1.0'
            },
            {
                'loc': url_for('main.about', _external=True),
                'lastmod': datetime.now().strftime('%Y-%m-%d'),
                'changefreq': 'monthly',
                'priority': '0.8'
            },
            {
                'loc': url_for('posts.index', _external=True),
                'lastmod': datetime.now().strftime('%Y-%m-%d'),
                'changefreq': 'daily',
                'priority': '0.9'
            }
        ]
        # Add post URLs (limit to 100 latest posts)
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            posts = get_all_text_posts(posts_dir)
            for post in posts[:100]:
                urls.append({
                    'loc': url_for('posts.view_by_slug', slug=post.slug, _external=True),
                    'lastmod': post.date.strftime('%Y-%m-%d'),
                    'changefreq': 'monthly',
                    'priority': '0.7'
                })
        except Exception as e:
            current_app.logger.warning(f'사이트맵 포스트 추가 실패: {e}')
        # Build XML
        xml_lines: List[str] = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]
        for u in urls:
            xml_lines.append('  <url>')
            xml_lines.append(f'    <loc>{u["loc"]}</loc>')
            xml_lines.append(f'    <lastmod>{u["lastmod"]}</lastmod>')
            xml_lines.append(f'    <changefreq>{u["changefreq"]}</changefreq>')
            xml_lines.append(f'    <priority>{u["priority"]}</priority>')
            xml_lines.append('  </url>')
        xml_lines.append('</urlset>')
        return Response('\n'.join(xml_lines), mimetype='application/xml')
    except Exception as e:
        current_app.logger.error(f'사이트맵 생성 오류: {e}')
        return Response('', status=500)

# Error handlers specific to this blueprint
@main_bp.errorhandler(404)
def main_not_found_error(error):
    current_app.logger.info(f'404 에러 (메인): {request.url}')
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def main_internal_error(error):
    current_app.logger.error(f'500 에러 (메인): {error}')
    return render_template('500.html'), 500
