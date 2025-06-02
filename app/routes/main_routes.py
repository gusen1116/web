# app/routes/main_routes.py
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
    """개선된 검색 API - 성능 최적화"""
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
        
        # 검색어 길이 제한
        if len(query) > 100:
            return jsonify({
                'error': '검색어가 너무 깁니다'
            }), 400
        
        # 검색 실행 - 개선된 알고리즘
        search_results = _perform_optimized_search(query, limit)
        
        return jsonify({
            'query': query,
            'results': search_results['results'],
            'total': search_results['total'],
            'limit': limit,
            'search_time': search_results.get('search_time', 0)
        })
        
    except Exception as e:
        current_app.logger.error(f'검색 API 오류: {e}')
        return jsonify({
            'error': '검색 중 오류가 발생했습니다'
        }), 500


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
                'url': f'/posts?tag={tag}'
            })
        
        return result
        
    except Exception as e:
        current_app.logger.error(f'인기 태그 처리 오류: {e}')
        return []


def _perform_optimized_search(query: str, limit: int) -> Dict[str, Any]:
    """
    최적화된 검색 실행 - 성능 개선
    
    개선사항:
    1. 캐시된 데이터 사용
    2. 검색어 전처리
    3. 점수 계산 최적화
    4. 조기 종료 조건
    """
    import time
    start_time = time.time()
    
    try:
        all_posts = CacheService.get_posts_with_cache()
        query_lower = query.lower()
        
        # 검색어 전처리 - 여러 단어 지원
        search_terms = [term.strip() for term in query_lower.split() if term.strip()]
        
        results = []
        
        for post in all_posts:
            score = 0
            
            # 캐시된 소문자 텍스트 사용 (성능 향상)
            title_lower = post.title.lower()
            content_lower = post.content.lower()
            author_lower = post.author.lower()
            tags_lower = [tag.lower() for tag in post.tags]
            
            # 각 검색어에 대해 점수 계산
            for term in search_terms:
                term_score = 0
                
                # 제목 매칭 (가중치 5)
                if term in title_lower:
                    term_score += 5
                    # 정확한 단어 매칭은 추가 점수
                    if f' {term} ' in f' {title_lower} ':
                        term_score += 2
                
                # 태그 매칭 (가중치 3)
                for tag_lower in tags_lower:
                    if term in tag_lower:
                        term_score += 3
                        break
                
                # 작성자 매칭 (가중치 2)
                if term in author_lower:
                    term_score += 2
                
                # 내용 매칭 (가중치 1)
                if term in content_lower:
                    term_score += 1
                    # 내용에서 여러 번 나타나는 경우 추가 점수 (최대 3점)
                    count = content_lower.count(term)
                    term_score += min(count - 1, 2)
                
                score += term_score
            
            # 모든 검색어가 포함된 경우 보너스 점수
            if len(search_terms) > 1:
                all_terms_found = all(
                    any(term in text for text in [title_lower, content_lower, author_lower] + tags_lower)
                    for term in search_terms
                )
                if all_terms_found:
                    score += 3
            
            # 점수가 있는 경우만 결과에 포함
            if score > 0:
                results.append({
                    'post': post,
                    'score': score
                })
                
                # 성능을 위한 조기 종료 (상위 100개만 계산)
                if len(results) >= 100:
                    break
        
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
                'preview': post.get_preview(150),
                'tags': post.tags[:3],
                'date': post.date.isoformat(),
                'url': post.get_url(),
                'score': item['score']
            })
        
        search_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        return {
            'results': formatted_results,
            'total': len(results),
            'search_time': search_time
        }
        
    except Exception as e:
        current_app.logger.error(f'검색 실행 오류: {e}')
        return {
            'results': [],
            'total': 0,
            'search_time': 0
        }


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
            for post in posts[:100]:  # 최대 100개만 사이트맵에 포함
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