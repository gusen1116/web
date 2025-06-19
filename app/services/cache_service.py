# app/services/cache_service.py
from flask import current_app
from flask_caching import Cache
from typing import List, Dict, Optional, Any
from app.services.text_service import get_all_text_posts, get_tags_count, TextPost

# Flask-Caching 인스턴스 (app/__init__.py에서 초기화됨)
from app import cache

class CacheService:
    """
    Redis 기반 캐시 서비스 - Flask-Caching 사용
    멀티프로세스 환경에서도 안정적으로 동작
    """
    
    # 캐시 키 상수
    CACHE_KEY_ALL_POSTS = 'all_posts'
    CACHE_KEY_TAGS_COUNT = 'tags_count'
    CACHE_KEY_POST_BY_SLUG = 'post_slug_{}'
    CACHE_KEY_STATS = 'cache_stats'
    
    @classmethod
    def get_posts_with_cache(cls, force_refresh: bool = False) -> List[TextPost]:
        """
        캐싱된 포스트 목록 반환
        
        Args:
            force_refresh: 강제 새로고침 여부
            
        Returns:
            List[TextPost]: 포스트 목록
        """
        if force_refresh:
            cache.delete(cls.CACHE_KEY_ALL_POSTS)
            cls._increment_stat('invalidations')
        
        # 캐시에서 조회
        posts = cache.get(cls.CACHE_KEY_ALL_POSTS)
        
        if posts is not None:
            cls._increment_stat('hits')
            return posts
        
        # 캐시 미스 - 새로 로드
        cls._increment_stat('misses')
        
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            posts = get_all_text_posts(posts_dir)
            
            # 캐시에 저장
            timeout = current_app.config.get('CACHE_TIMEOUT', 600)
            cache.set(cls.CACHE_KEY_ALL_POSTS, posts, timeout=timeout)
            
            # 개별 포스트도 캐시 (슬러그 기반 조회용)
            for post in posts:
                if hasattr(post, 'slug') and post.slug:
                    cache_key = cls.CACHE_KEY_POST_BY_SLUG.format(post.slug)
                    cache.set(cache_key, post, timeout=timeout)
            
            current_app.logger.debug(f'포스트 캐시 새로고침 완료: {len(posts)}개')
            return posts
            
        except Exception as e:
            current_app.logger.error(f'포스트 캐시 로드 오류: {e}')
            return []
    
    @classmethod
    def get_post_by_slug(cls, slug: str) -> Optional[TextPost]:
        """
        슬러그로 포스트 조회 - 캐시 활용
        
        Args:
            slug: 포스트 슬러그
            
        Returns:
            Optional[TextPost]: 포스트 객체 또는 None
        """
        # 개별 포스트 캐시에서 조회
        cache_key = cls.CACHE_KEY_POST_BY_SLUG.format(slug)
        post = cache.get(cache_key)
        
        if post is not None:
            cls._increment_stat('hits')
            return post
        
        # 전체 포스트 목록에서 검색
        all_posts = cls.get_posts_with_cache()
        
        # 다양한 형식으로 매칭 시도
        slug_no_ext = slug.rsplit('.', 1)[0] if '.' in slug else slug
        
        for post in all_posts:
            if (hasattr(post, 'slug') and post.slug == slug) or \
               post.id == slug_no_ext or \
               post.filename == slug or \
               post.filename == slug + '.txt':
                # 찾은 포스트를 개별 캐시에 저장
                timeout = current_app.config.get('CACHE_TIMEOUT', 600)
                cache.set(cache_key, post, timeout=timeout)
                return post
        
        return None
    
    @classmethod
    def get_tags_with_cache(cls, force_refresh: bool = False) -> Dict[str, int]:
        """
        캐싱된 태그 카운트 반환
        
        Args:
            force_refresh: 강제 새로고침 여부
            
        Returns:
            Dict[str, int]: 태그 카운트
        """
        if force_refresh:
            cache.delete(cls.CACHE_KEY_TAGS_COUNT)
            cls._increment_stat('invalidations')
        
        # 캐시에서 조회
        tags_count = cache.get(cls.CACHE_KEY_TAGS_COUNT)
        
        if tags_count is not None:
            cls._increment_stat('hits')
            return tags_count
        
        # 캐시 미스 - 새로 로드
        cls._increment_stat('misses')
        
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            tags_count = get_tags_count(posts_dir)
            
            # 캐시에 저장
            timeout = current_app.config.get('CACHE_TIMEOUT', 600)
            cache.set(cls.CACHE_KEY_TAGS_COUNT, tags_count, timeout=timeout)
            
            current_app.logger.debug(f'태그 캐시 새로고침 완료: {len(tags_count)}개')
            return tags_count
            
        except Exception as e:
            current_app.logger.error(f'태그 캐시 로드 오류: {e}')
            return {}
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        stats = cache.get(cls.CACHE_KEY_STATS) or {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }
        
        total_requests = stats['hits'] + stats['misses']
        hit_rate = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # 현재 캐시된 항목 수 계산
        all_posts = cache.get(cls.CACHE_KEY_ALL_POSTS)
        tags_count = cache.get(cls.CACHE_KEY_TAGS_COUNT)
        
        return {
            'hits': stats['hits'],
            'misses': stats['misses'],
            'invalidations': stats['invalidations'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'posts_cached': len(all_posts) if all_posts else 0,
            'tags_cached': len(tags_count) if tags_count else 0,
            'cache_type': current_app.config.get('CACHE_TYPE', 'unknown')
        }
    
    @classmethod
    def clear_cache(cls) -> None:
        """전체 캐시 초기화"""
        cache.clear()
        current_app.logger.info('캐시 전체 초기화 완료')
    
    @classmethod
    def invalidate_posts_cache(cls) -> None:
        """포스트 관련 캐시만 무효화"""
        cache.delete(cls.CACHE_KEY_ALL_POSTS)
        # 개별 포스트 캐시도 삭제 (패턴 매칭)
        # Flask-Caching은 패턴 삭제를 직접 지원하지 않으므로,
        # 전체 캐시를 지우거나 Redis 직접 접근이 필요
        cls._increment_stat('invalidations')
    
    @classmethod
    def _increment_stat(cls, stat_name: str) -> None:
        """통계 카운터 증가"""
        stats = cache.get(cls.CACHE_KEY_STATS) or {
            'hits': 0,
            'misses': 0,
            'invalidations': 0
        }
        
        if stat_name in stats:
            stats[stat_name] += 1
            cache.set(cls.CACHE_KEY_STATS, stats, timeout=None)  # 통계는 만료 없음