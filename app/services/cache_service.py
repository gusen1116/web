# app/services/cache_service.py
from flask import current_app
from typing import List, Dict, Optional, Any
from app.services.text_service import get_all_text_posts, get_text_post, get_tags_count, TextPost
from app import cache

class CacheService:
    """Redis‑backed caching service using Flask‑Caching."""
    CACHE_KEY_ALL_POSTS = 'all_posts'
    CACHE_KEY_TAGS_COUNT = 'tags_count'
    CACHE_KEY_POST_BY_SLUG = 'post_slug_{}'
    CACHE_KEY_STATS = 'cache_stats'

    @classmethod
    def get_posts_with_cache(cls, force_refresh: bool = False) -> List[TextPost]:
        """Return a list of all posts, optionally forcing a refresh."""
        if force_refresh:
            cache.delete(cls.CACHE_KEY_ALL_POSTS)
            cls._increment_stat('invalidations')
        
        posts = cache.get(cls.CACHE_KEY_ALL_POSTS)
        if posts is not None:
            cls._increment_stat('hits')
            return posts
        
        cls._increment_stat('misses')
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            posts = get_all_text_posts(posts_dir)
            timeout = current_app.config.get('CACHE_TIMEOUT', 600)
            cache.set(cls.CACHE_KEY_ALL_POSTS, posts, timeout=timeout)
            
            # 개별 포스트도 캐시에 저장
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
    def get_post_by_slug_with_cache(cls, slug: str) -> Optional[TextPost]:
        """Return a single post by its slug, using the cache if possible."""
        cache_key = cls.CACHE_KEY_POST_BY_SLUG.format(slug)
        post = cache.get(cache_key)
        
        if post is not None:
            cls._increment_stat('hits')
            return post
            
        cls._increment_stat('misses')
        # 캐시에 없으면 파일 시스템에서 직접 로드
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            # slug와 일치하는 파일명을 찾아 로드 (확장자 고려)
            all_posts = get_all_text_posts(posts_dir)
            for p in all_posts:
                if p.slug == slug or p.id == slug:
                    timeout = current_app.config.get('CACHE_TIMEOUT', 600)
                    cache.set(cache_key, p, timeout=timeout)
                    return p
            return None
        except Exception as e:
            current_app.logger.error(f"'{slug}' 포스트 로드 오류: {e}")
            return None

    @classmethod
    def get_tags_with_cache(cls, force_refresh: bool = False) -> Dict[str, int]:
        """Return a dict of tag counts, optionally forcing a refresh."""
        if force_refresh:
            cache.delete(cls.CACHE_KEY_TAGS_COUNT)
            cls._increment_stat('invalidations')
        
        tags_count = cache.get(cls.CACHE_KEY_TAGS_COUNT)
        if tags_count is not None:
            cls._increment_stat('hits')
            return tags_count
        
        cls._increment_stat('misses')
        try:
            posts = cls.get_posts_with_cache() # 전체 포스트 캐시 활용
            tags_count = {}
            for post in posts:
                for tag in post.tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
            
            timeout = current_app.config.get('CACHE_TIMEOUT', 600)
            cache.set(cls.CACHE_KEY_TAGS_COUNT, tags_count, timeout=timeout)
            current_app.logger.debug(f'태그 캐시 새로고침 완료: {len(tags_count)}개')
            return tags_count
        except Exception as e:
            current_app.logger.error(f'태그 캐시 로드 오류: {e}')
            return {}

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Return cache hit/miss statistics."""
        stats = cache.get(cls.CACHE_KEY_STATS) or {
            'hits': 0, 'misses': 0, 'invalidations': 0
        }
        total_requests = stats['hits'] + stats['misses']
        hit_rate = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
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
        """Clear the entire cache."""
        cache.clear()
        current_app.logger.info('캐시 전체 초기화 완료')

    @classmethod
    def invalidate_posts_cache(cls) -> None:
        """Invalidate only the posts-related caches."""
        cache.delete(cls.CACHE_KEY_ALL_POSTS)
        # 개별 포스트 캐시도 함께 삭제하는 로직 추가 가능
        cls._increment_stat('invalidations')

    @classmethod
    def _increment_stat(cls, stat_name: str) -> None:
        """Increment a statistic counter stored in the cache."""
        stats = cache.get(cls.CACHE_KEY_STATS) or {
            'hits': 0, 'misses': 0, 'invalidations': 0
        }
        if stat_name in stats:
            stats[stat_name] += 1
            cache.set(cls.CACHE_KEY_STATS, stats, timeout=None)