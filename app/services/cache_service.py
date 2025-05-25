# app/services/cache_service.py
import os
import time
import hashlib
from flask import current_app
from app import cache

class CacheService:
    """파일 기반 캐싱 서비스"""
    
    @staticmethod
    def get_posts_with_cache():
        """캐시된 포스트 목록 반환"""
        cache_key = CacheService._get_posts_cache_key()
        
        # 캐시에서 확인
        cached_posts = cache.get(cache_key)
        if cached_posts and CacheService._is_cache_valid():
            return cached_posts
        
        # 캐시 미스 시 새로 로드
        from app.services.file_service import FileService
        posts = FileService.get_all_text_posts()
        
        # 캐시에 저장
        cache.set(cache_key, posts, timeout=current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))
        CacheService._update_cache_timestamp()
        
        return posts
    
    @staticmethod
    def get_post_with_cache(slug_or_id):
        """캐시된 단일 포스트 반환"""
        cache_key = f"post:{slug_or_id}"
        
        cached_post = cache.get(cache_key)
        if cached_post:
            return cached_post
        
        # 모든 포스트에서 찾기
        posts = CacheService.get_posts_with_cache()
        matching_post = None
        
        for post in posts:
            if (post.slug == slug_or_id or 
                post.id == slug_or_id or 
                post.filename == f"{slug_or_id}.txt"):
                matching_post = post
                break
        
        if matching_post:
            cache.set(cache_key, matching_post, timeout=300)
        
        return matching_post
    
    @staticmethod
    def get_tags_with_cache():
        """캐시된 태그 목록 반환"""
        cache_key = "tags_count"
        
        cached_tags = cache.get(cache_key)
        if cached_tags and CacheService._is_cache_valid():
            return cached_tags
        
        from app.services.file_service import FileService
        tags = FileService.get_tags_count()
        
        cache.set(cache_key, tags, timeout=300)
        return tags
    
    @staticmethod
    def get_rendered_content_with_cache(post):
        """캐시된 렌더링 콘텐츠 반환"""
        content_hash = CacheService._get_content_hash(post.content)
        cache_key = f"rendered:{post.id}:{content_hash}"
        
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
        
        from app.services.content_service import ContentService
        rendered = ContentService.render_content(post.content)
        
        cache.set(cache_key, rendered, timeout=600)  # 10분
        return rendered
    
    @staticmethod
    def invalidate_cache():
        """캐시 무효화"""
        cache.clear()
        CacheService._update_cache_timestamp()
        current_app.logger.info("캐시가 무효화되었습니다")
    
    @staticmethod
    def _get_posts_cache_key():
        """포스트 캐시 키 생성"""
        return "all_posts"
    
    @staticmethod
    def _is_cache_valid():
        """캐시 유효성 검사"""
        posts_dir = current_app.config['POSTS_DIR']
        
        if not os.path.exists(posts_dir):
            return False
        
        # 디렉토리 수정 시간 확인
        dir_mtime = os.path.getmtime(posts_dir)
        cache_timestamp = cache.get('cache_timestamp', 0)
        
        return dir_mtime <= cache_timestamp
    
    @staticmethod
    def _update_cache_timestamp():
        """캐시 타임스탬프 업데이트"""
        cache.set('cache_timestamp', time.time(), timeout=3600)
    
    @staticmethod
    def _get_content_hash(content):
        """콘텐츠 해시 생성"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
    
    @staticmethod
    def warm_up_cache():
        """캐시 예열"""
        try:
            CacheService.get_posts_with_cache()
            CacheService.get_tags_with_cache()
            current_app.logger.info("캐시 예열 완료")
        except Exception as e:
            current_app.logger.error(f"캐시 예열 실패: {str(e)}")
    
    @staticmethod
    def get_cache_stats():
        """캐시 통계 반환 (디버그용)"""
        if hasattr(cache.cache, '_cache'):
            return {
                'cache_size': len(cache.cache._cache),
                'cache_hits': getattr(cache.cache, 'hits', 0),
                'cache_misses': getattr(cache.cache, 'misses', 0)
            }
        return {'status': 'unavailable'}