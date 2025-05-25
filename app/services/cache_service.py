# app/services/cache_service.py
import time
from flask import current_app
from app.services.text_service import get_all_text_posts, get_tags_count
import threading

class CacheService:
    """캐시 서비스 - 포스트와 태그 데이터를 메모리에 캐싱"""
    
    _posts_cache = None
    _tags_cache = None
    _cache_timestamp = None
    _lock = threading.Lock()
    
    @classmethod
    def get_posts_with_cache(cls):
        """캐싱된 포스트 목록 반환"""
        with cls._lock:
            cache_timeout = current_app.config.get('CACHE_TIMEOUT', 300)
            now = time.time()
            
            # 캐시가 유효한지 확인
            if (cls._posts_cache is not None and 
                cls._cache_timestamp is not None and 
                (now - cls._cache_timestamp) < cache_timeout):
                return cls._posts_cache[:]
            
            # 캐시 갱신
            posts_dir = current_app.config.get('POSTS_DIR')
            cls._posts_cache = get_all_text_posts(posts_dir)
            cls._cache_timestamp = now
            
            return cls._posts_cache[:]
    
    @classmethod
    def get_tags_with_cache(cls):
        """캐싱된 태그 카운트 반환"""
        with cls._lock:
            cache_timeout = current_app.config.get('CACHE_TIMEOUT', 300)
            now = time.time()
            
            # 캐시가 유효한지 확인
            if (cls._tags_cache is not None and 
                cls._cache_timestamp is not None and 
                (now - cls._cache_timestamp) < cache_timeout):
                return cls._tags_cache.copy()
            
            # 캐시 갱신
            posts_dir = current_app.config.get('POSTS_DIR')
            cls._tags_cache = get_tags_count(posts_dir)
            cls._cache_timestamp = now
            
            return cls._tags_cache.copy()
    
    @classmethod
    def clear_cache(cls):
        """캐시 초기화"""
        with cls._lock:
            cls._posts_cache = None
            cls._tags_cache = None
            cls._cache_timestamp = None