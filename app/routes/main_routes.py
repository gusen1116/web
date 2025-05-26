# app/routes/main_routes.py
from flask import Blueprint, render_template, current_app, jsonify, request
from typing import List, Dict, Any
from app.services.cache_service import CacheService
from app.services.text_service import TextPost

# 블루프린트 생성
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    메인 페이지 - 성능 최적화 및 안전성 강화
    
    주요 개선사항:
    - 캐시 서비스 활용으로 성능 향상
    - 예외 처리 강화
    - 데이터 검증 및 안전한 렌더링
    """
    try:
        # 캐시된 데이터 가져오기 (성능 최적화)
        all_posts = CacheService.get_posts_with_cache()
        
        # 최근 포스트 선별 (메인 페이지용 - 상위 3개)
        recent_posts = _get_recent_posts(all_posts, limit=3)
        
        # 인기 태그 가져오기 (상위 10개)
        popular_tags = _get_popular_tags(limit=10)
        
        # 템플릿 렌더링
        return render_template(
            'index.html',
            posts=all_posts,  # 템플릿 호환성을 위해 유지
            recent_posts=recent_posts,
            popular_tags=popular_tags
        )
        
    except Exception as e:
        current_app.logger.error(f'메인 페이지 로드 에러: {e}')
        
        # 오류 발생 시에도 빈 데이터로 페이지 표시 (가용성 확보)
        return render_template(
            'index.html', 
            posts=[], 
            recent_posts=[], 
            popular_tags=[],
            error_message="일시적으로 콘텐츠를 불러올 수 없습니다."
        )


@main_bp.route('/about')
def about():
    """소개 페이지 - 정적 페이지"""
    try:
        return render_template('about.html')
    except Exception as e:
        current_app.logger.error(f'소개 페이지 로드 에러: {e}')
        return render_template('404.html'), 500


@main_bp.route('/api/status')
def api_status():
    """
    시스템 상태 API - 헬스체크 및 기본 통계
    
    Returns:
        JSON: 시스템 상태 정보
    """
    try:
        # 기본 시스템 정보
        status_info = {
            'status': 'healthy',
            'version': '2.0.0',
            'environment': 'production'
        }
        
        # 캐시 통계 추가
        try:
            cache_stats = CacheService.get_cache_stats()
            status_info['cache'] = {
                'hit_rate': cache_stats.get('hit_rate', 0),
                'posts_cached': cache_stats.get('posts_cached', 0),
                'tags_cached': cache_stats.get('tags_cached', 0),
                'memory_usage': cache_stats.get('memory_usage', 'unknown')
            }
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


@main_bp.route('/api/search')
def api_search():
    """
    간단한 검색 API - 제목과 태그 기반 검색
    
    Query Parameters:
        q: 검색어
        limit: 결과 수 제한 (기본 10, 최대 50)
    
    Returns:
        JSON: 검색 결과
    """
    try:
        # 검색어 추출 및 검증
        query = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if not query:
            return jsonify({
                'query': '',
                'results': [],
                'total': 0,
                'message': '검색어를 입력해주세요'
            })
        
        # 검색어 길이 제한 (보안 및 성능)
        if len(query) > 100:
            return jsonify({
                'error': '검색어가 너무 깁니다'
            }), 400
        
        # 검색 실행
        search_results = _perform_search(query, limit)
        
        return jsonify({
            'query': query,
            'results': search_results['results'],
            'total': search_results['total'],
            'limit': limit
        })
        
    except Exception as e:
        current_app.logger.error(f'검색 API 오류: {e}')
        return jsonify({
            'error': '검색 중 오류가 발생했습니다'
        }), 500


def _get_recent_posts(posts: List[TextPost], limit: int = 3) -> List[Dict[str, Any]]:
    """
    최근 포스트 가져오기 - 템플릿용 데이터 변환
    
    Args:
        posts: 전체 포스트 리스트
        limit: 반환할 포스트 수
    
    Returns:
        List[Dict]: 템플릿용 포스트 데이터
    """
    try:
        recent = posts[:limit] if posts else []
        
        # 템플릿에서 사용하기 쉬운 형태로 변환
        result = []
        for post in recent:
            result.append({
                'id': post.id,
                'title': str(post.title),
                'slug': post.slug,
                'date': post.date,
                'author': str(post.author),
                'tags': post.tags[:3],  # 최대 3개 태그만
                'preview': post.get_preview(150),
                'url': post.get_url(),
                'word_count': post.get_word_count()
            })
        
        return result
        
    except Exception as e:
        current_app.logger.error(f'최근 포스트 처리 오류: {e}')
        return []


def _get_popular_tags(limit: int = 10) -> List[Dict[str, Any]]:
    """
    인기 태그 가져오기 - 사용 빈도 기준
    
    Args:
        limit: 반환할 태그 수
    
    Returns:
        List[Dict]: 인기 태그 데이터
    """
    try:
        tags_count = CacheService.get_tags_with_cache()
        
        # 사용 빈도 기준 정렬
        sorted_tags = sorted(
            tags_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        # 템플릿용 데이터 변환
        result = []
        for tag, count in sorted_tags:
            result.append({
                'name': tag,
                'count': count,
                'url': f'/posts?tag={tag}'
            })
        
        return result
        
    except Exception as e:
        current_app.logger.error(f'인기 태그 처리 오류: {e}')
        return []


def _perform_search(query: str, limit: int) -> Dict[str, Any]:
    """
    검색 실행 - 제목, 태그, 내용 기반 검색
    
    Args:
        query: 검색어
        limit: 결과 수 제한
    
    Returns:
        Dict: 검색 결과
    """
    try:
        all_posts = CacheService.get_posts_with_cache()
        query_lower = query.lower()
        
        # 검색 결과 저장용
        results = []
        
        for post in all_posts:
            score = 0
            
            # 제목 매칭 (가중치 3)
            if query_lower in post.title.lower():
                score += 3
            
            # 태그 매칭 (가중치 2)
            for tag in post.tags:
                if query_lower in tag.lower():
                    score += 2
                    break
            
            # 내용 매칭 (가중치 1)
            if query_lower in post.content.lower():
                score += 1
            
            # 작성자 매칭 (가중치 1)
            if query_lower in post.author.lower():
                score += 1
            
            # 점수가 있는 경우만 결과에 포함
            if score > 0:
                results.append({
                    'post': post,
                    'score': score
                })
        
        # 점수 기준 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 제한된 결과 변환
        limited_results = results[:limit]
        formatted_results = []
        
        for item in limited_results:
            post = item['post']
            formatted_results.append({
                'id': post.id,
                'title': str(post.title),
                'slug': post.slug,
                'preview': post.get_preview(100),
                'tags': post.tags[:3],
                'date': post.date.isoformat(),
                'url': post.get_url(),
                'score': item['score']
            })
        
        return {
            'results': formatted_results,
            'total': len(results)
        }
        
    except Exception as e:
        current_app.logger.error(f'검색 실행 오류: {e}')
        return {
            'results': [],
            'total': 0
        }


@main_bp.route('/robots.txt')
def robots_txt():
    """
    robots.txt 파일 제공 - SEO 최적화
    
    Returns:
        Response: robots.txt 내용
    """
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
    """
    사이트맵 XML 생성 - SEO 최적화
    
    Returns:
        Response: XML 사이트맵
    """
    try:
        from flask import Response, url_for, request
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
            for post in posts:
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


# ===== 에러 핸들러 (메인 블루프린트용) =====

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