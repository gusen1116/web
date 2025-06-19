# app/routes/main_routes.py (태그 중심으로 개편)
from flask import Blueprint, render_template, current_app, jsonify, request
from typing import List, Dict, Any
from app.services.cache_service import CacheService
from app.services.text_service import TextPost

# 블루프린트 생성
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """메인 페이지 - 성능 최적화 및 안전성 강화"""
    try:
        # 캐시된 데이터 가져오기
        all_posts = CacheService.get_posts_with_cache()
        
        # 최근 포스트 선별 (상위 3개)
        recent_posts = all_posts[:3] if all_posts else []
        
        # 인기 태그 가져오기 (상위 10개)
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
    """소개 페이지"""
    try:
        return render_template('about.html')
    except Exception as e:
        current_app.logger.error(f'소개 페이지 로드 에러: {e}')
        return render_template('404.html'), 500


@main_bp.route('/api/status')
def api_status():
    """시스템 상태 API"""
    try:
        status_info = {
            'status': 'healthy',
            'version': '2.0.0',
            'environment': current_app.config.get('FLASK_ENV', 'production'),
            'cache_type': current_app.config.get('CACHE_TYPE', 'unknown')
        }
        
        # 캐시 통계 추가
        try:
            cache_stats = CacheService.get_cache_stats()
            status_info['cache'] = cache_stats
        except Exception as cache_error:
            current_app.logger.warning(f'캐시 통계 수집 실패: {cache_error}')
            status_info['cache'] = {'status': 'unavailable'}
        
        # 콘텐츠 통계 추가
        try:
            all_posts = CacheService.get_posts_with_cache()
            tags_count = CacheService.get_tags_with_cache()
            
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
        return jsonify({
            'status': 'error',
            'message': '시스템 상태를 확인할 수 없습니다'
        }), 500


@main_bp.route('/api/tags')
def api_tags():
    """태그 관련 API - 태그 목록과 통계 제공"""
    try:
        tags_count = CacheService.get_tags_with_cache()
        
        # 태그를 인기도순으로 정렬
        sorted_tags = sorted(
            tags_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 태그 클라우드를 위한 데이터 생성
        max_count = sorted_tags[0][1] if sorted_tags else 1
        min_count = sorted_tags[-1][1] if sorted_tags else 1
        
        tag_cloud = []
        for tag, count in sorted_tags:
            # 태그 크기 계산 (1-5 레벨)
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
def api_related_tags(tag):
    """특정 태그와 함께 자주 사용되는 태그 찾기"""
    try:
        all_posts = CacheService.get_posts_with_cache()
        
        # 해당 태그를 가진 포스트 찾기
        posts_with_tag = [p for p in all_posts if tag in p.tags]
        
        if not posts_with_tag:
            return jsonify({'related_tags': []})
        
        # 관련 태그 카운트
        related_tags = {}
        for post in posts_with_tag:
            for other_tag in post.tags:
                if other_tag != tag:  # 자기 자신 제외
                    related_tags[other_tag] = related_tags.get(other_tag, 0) + 1
        
        # 빈도순 정렬
        sorted_related = sorted(
            related_tags.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]  # 상위 10개
        
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
    """인기 태그 가져오기"""
    try:
        tags_count = CacheService.get_tags_with_cache()
        
        sorted_tags = sorted(
            tags_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        result = []
        for tag, count in sorted_tags:
            result.append({
                'name': tag,
                'count': count,
                'url': f'/posts/tag/{tag}'
            })
        
        return result
        
    except Exception as e:
        current_app.logger.error(f'인기 태그 처리 오류: {e}')
        return []


@main_bp.route('/robots.txt')
def robots_txt():
    """robots.txt 파일 제공"""
    from flask import Response
    
    robots_content = """User-agent: *
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
def sitemap_xml():
    """사이트맵 XML 생성"""
    try:
        from flask import Response, url_for
        from datetime import datetime
        
        # 기본 페이지들
        urls = [
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
        
        # 포스트 페이지들 추가
        try:
            posts = CacheService.get_posts_with_cache()
            for post in posts[:100]:
                urls.append({
                    'loc': url_for('posts.view_by_slug', slug=post.slug, _external=True),
                    'lastmod': post.date.strftime('%Y-%m-%d'),
                    'changefreq': 'monthly',
                    'priority': '0.7'
                })
        except Exception as e:
            current_app.logger.warning(f'사이트맵 포스트 추가 실패: {e}')
        
        # XML 생성
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for url in urls:
            xml_content.append('  <url>')
            xml_content.append(f'    <loc>{url["loc"]}</loc>')
            xml_content.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
            xml_content.append(f'    <changefreq>{url["changefreq"]}</changefreq>')
            xml_content.append(f'    <priority>{url["priority"]}</priority>')
            xml_content.append('  </url>')
        
        xml_content.append('</urlset>')
        
        return Response('\n'.join(xml_content), mimetype='application/xml')
        
    except Exception as e:
        current_app.logger.error(f'사이트맵 생성 오류: {e}')
        return Response('', status=500)


# 에러 핸들러
@main_bp.errorhandler(404)
def not_found_error(error):
    """404 에러 핸들러"""
    current_app.logger.info(f'404 에러 (메인): {request.url}')
    return render_template('404.html'), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    current_app.logger.error(f'500 에러 (메인): {error}')
    return render_template('500.html'), 500 