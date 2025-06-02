# app/services/cache_service.py
import time
import hashlib
import threading
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from flask import current_app
from app.services.text_service import get_all_text_posts, get_tags_count, TextPost


class CacheService:
    """
    개선된 캐시 서비스 - 파일 해시 기반 변경 감지 및 포스트 인덱싱
    
    주요 개선사항:
    - 파일 해시 기반 정확한 변경 감지
    - 포스트 인덱싱으로 O(1) 조회
    - 멀티프로세스 환경 대응
    - 메모리 사용량 최적화
    """
    
    # 클래스 레벨 캐시 저장소
    _posts_cache: Optional[List[TextPost]] = None
    _tags_cache: Optional[Dict[str, int]] = None
    _posts_index: Dict[str, TextPost] = {}  # 빠른 조회를 위한 인덱스
    _cache_metadata: Dict[str, Any] = {}
    _cache_stats: Dict[str, int] = {'hits': 0, 'misses': 0, 'invalidations': 0}
    
    # 스레드 안전성을 위한 락
    _lock = threading.RLock()  # 재귀 락 사용
    
    # 캐시 설정
    _cache_ttl: int = 600  # 기본 TTL: 10분
    _max_cache_size: int = 1000  # 최대 캐시 항목 수
    
    @classmethod
    def configure(cls, cache_timeout: Optional[int] = None, max_size: Optional[int] = None) -> None:
        """캐시 설정 구성"""
        with cls._lock:
            if cache_timeout is not None:
                cls._cache_ttl = max(60, cache_timeout)  # 최소 1분
            if max_size is not None:
                cls._max_cache_size = max(100, max_size)  # 최소 100개
            
            # 설정 변경 시 캐시 초기화
            cls._invalidate_all_cache()
            current_app.logger.info(f'캐시 설정 업데이트: TTL={cls._cache_ttl}s, 최대크기={cls._max_cache_size}')
    
    @classmethod
    def get_posts_with_cache(cls, force_refresh: bool = False) -> List[TextPost]:
        """
        캐싱된 포스트 목록 반환 - 파일 해시 기반 스마트 캐시 무효화
        
        Args:
            force_refresh: 강제 새로고침 여부
            
        Returns:
            List[TextPost]: 포스트 목록 (복사본)
        """
        with cls._lock:
            # 강제 새로고침 요청 시
            if force_refresh:
                cls._invalidate_posts_cache()
                cls._cache_stats['invalidations'] += 1
            
            # 캐시 유효성 검사
            if cls._is_posts_cache_valid():
                cls._cache_stats['hits'] += 1
                return cls._get_posts_copy()
            
            # 캐시 미스 - 새로 로드
            cls._cache_stats['misses'] += 1
            return cls._refresh_posts_cache()
    
    @classmethod
    def get_post_by_slug(cls, slug: str) -> Optional[TextPost]:
        """
        슬러그로 포스트 빠르게 조회 - O(1) 성능
        
        Args:
            slug: 포스트 슬러그
            
        Returns:
            Optional[TextPost]: 포스트 객체 또는 None
        """
        with cls._lock:
            # 캐시가 유효한지 확인
            if not cls._is_posts_cache_valid():
                cls._refresh_posts_cache()
            
            # 인덱스에서 조회
            # 1. 슬러그로 직접 조회
            if slug in cls._posts_index:
                return cls._posts_index[slug]
            
            # 2. 확장자 제거 후 조회
            slug_no_ext = slug.rsplit('.', 1)[0] if '.' in slug else slug
            if slug_no_ext in cls._posts_index:
                return cls._posts_index[slug_no_ext]
            
            # 3. .txt 확장자 추가 후 조회
            if f"{slug}.txt" in cls._posts_index:
                return cls._posts_index[f"{slug}.txt"]
            
            return None
    
    @classmethod
    def get_tags_with_cache(cls, force_refresh: bool = False) -> Dict[str, int]:
        """
        캐싱된 태그 카운트 반환
        
        Args:
            force_refresh: 강제 새로고침 여부
            
        Returns:
            Dict[str, int]: 태그 카운트 (복사본)
        """
        with cls._lock:
            # 강제 새로고침 요청 시
            if force_refresh:
                cls._invalidate_tags_cache()
                cls._cache_stats['invalidations'] += 1
            
            # 캐시 유효성 검사
            if cls._is_tags_cache_valid():
                cls._cache_stats['hits'] += 1
                return cls._get_tags_copy()
            
            # 캐시 미스 - 새로 로드
            cls._cache_stats['misses'] += 1
            return cls._refresh_tags_cache()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        with cls._lock:
            total_requests = cls._cache_stats['hits'] + cls._cache_stats['misses']
            hit_rate = (cls._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'hits': cls._cache_stats['hits'],
                'misses': cls._cache_stats['misses'],
                'invalidations': cls._cache_stats['invalidations'],
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests,
                'posts_cached': len(cls._posts_cache) if cls._posts_cache else 0,
                'posts_indexed': len(cls._posts_index),
                'tags_cached': len(cls._tags_cache) if cls._tags_cache else 0,
                'memory_usage': cls._estimate_memory_usage()
            }
    
    @classmethod
    def clear_cache(cls) -> None:
        """전체 캐시 초기화"""
        with cls._lock:
            cls._invalidate_all_cache()
            cls._cache_stats = {'hits': 0, 'misses': 0, 'invalidations': 0}
            current_app.logger.info('캐시 전체 초기화 완료')
    
    @classmethod  
    def invalidate_if_needed(cls) -> bool:
        """
        필요시 캐시 무효화 - 파일 시스템 변경 감지
        
        Returns:
            bool: 캐시가 무효화되었는지 여부
        """
        with cls._lock:
            posts_dir = Path(current_app.config.get('POSTS_DIR', ''))
            
            if not posts_dir.exists():
                return False
            
            # 현재 파일 해시 계산
            current_files_hash = cls._calculate_directory_hash(posts_dir)
            cached_files_hash = cls._cache_metadata.get('files_hash', '')
            
            # 변경 감지
            if current_files_hash != cached_files_hash:
                cls._invalidate_all_cache()
                cls._cache_stats['invalidations'] += 1
                current_app.logger.info('파일 시스템 변경 감지로 캐시 무효화')
                return True
            
            return False
    
    # ===== 내부 메서드들 =====
    
    @classmethod
    def _is_posts_cache_valid(cls) -> bool:
        """포스트 캐시 유효성 검사 - 파일 해시 기반"""
        if cls._posts_cache is None:
            return False
        
        # TTL 확인
        cache_time = cls._cache_metadata.get('posts_cache_time', 0)
        if time.time() - cache_time > cls._cache_ttl:
            return False
        
        # 파일 해시 기반 변경 확인
        posts_dir = Path(current_app.config.get('POSTS_DIR', ''))
        if not posts_dir.exists():
            return False
        
        current_files_hash = cls._calculate_directory_hash(posts_dir)
        cached_files_hash = cls._cache_metadata.get('files_hash', '')
        
        return current_files_hash == cached_files_hash
    
    @classmethod
    def _is_tags_cache_valid(cls) -> bool:
        """태그 캐시 유효성 검사"""
        if cls._tags_cache is None:
            return False
        
        # TTL 확인
        cache_time = cls._cache_metadata.get('tags_cache_time', 0)
        if time.time() - cache_time > cls._cache_ttl:
            return False
        
        # 포스트 캐시와 동일한 파일 해시 사용
        return cls._is_posts_cache_valid()
    
    @classmethod
    def _refresh_posts_cache(cls) -> List[TextPost]:
        """포스트 캐시 새로고침 - 인덱싱 포함"""
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            posts = get_all_text_posts(posts_dir)
            
            # 메모리 사용량 제한
            if len(posts) > cls._max_cache_size:
                posts = posts[:cls._max_cache_size]
                current_app.logger.warning(f'포스트 수가 최대 캐시 크기를 초과하여 {cls._max_cache_size}개로 제한')
            
            # 포스트 인덱스 생성
            cls._posts_index.clear()
            for post in posts:
                # 여러 키로 인덱싱 (빠른 조회를 위해)
                if hasattr(post, 'slug') and post.slug:
                    cls._posts_index[post.slug] = post
                cls._posts_index[post.id] = post
                cls._posts_index[post.filename] = post
                
                # 확장자 없는 파일명으로도 인덱싱
                filename_no_ext = post.filename.rsplit('.', 1)[0] if '.' in post.filename else post.filename
                cls._posts_index[filename_no_ext] = post
            
            # 캐시 업데이트
            cls._posts_cache = posts
            posts_dir_path = Path(posts_dir)
            current_time = time.time()
            
            cls._cache_metadata.update({
                'posts_cache_time': current_time,
                'files_hash': cls._calculate_directory_hash(posts_dir_path),
                'posts_count': len(posts)
            })
            
            current_app.logger.debug(f'포스트 캐시 새로고침 완료: {len(posts)}개, 인덱스: {len(cls._posts_index)}개')
            return cls._get_posts_copy()
            
        except Exception as e:
            current_app.logger.error(f'포스트 캐시 새로고침 오류: {e}')
            # 오류 시 빈 목록 반환
            cls._posts_cache = []
            cls._posts_index.clear()
            return []
    
    @classmethod
    def _refresh_tags_cache(cls) -> Dict[str, int]:
        """태그 캐시 새로고침"""
        try:
            posts_dir = current_app.config.get('POSTS_DIR')
            tags_count = get_tags_count(posts_dir)
            
            # 메모리 사용량 제한 - 상위 태그만 캐시
            if len(tags_count) > cls._max_cache_size // 2:
                # 사용 빈도 기준으로 상위 태그만 유지
                sorted_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)
                tags_count = dict(sorted_tags[:cls._max_cache_size // 2])
                current_app.logger.warning(f'태그 수가 많아 상위 {len(tags_count)}개만 캐시')
            
            # 캐시 업데이트
            cls._tags_cache = tags_count
            current_time = time.time()
            cls._cache_metadata.update({
                'tags_cache_time': current_time,
                'tags_count': len(tags_count)
            })
            
            current_app.logger.debug(f'태그 캐시 새로고침 완료: {len(tags_count)}개')
            return cls._get_tags_copy()
            
        except Exception as e:
            current_app.logger.error(f'태그 캐시 새로고침 오류: {e}')
            # 오류 시 빈 딕셔너리 반환
            cls._tags_cache = {}
            return {}
    
    @classmethod
    def _get_posts_copy(cls) -> List[TextPost]:
        """포스트 목록 복사본 반환 - 원본 보호"""
        if cls._posts_cache is None:
            return []
        
        # 얕은 복사로 성능 최적화 (TextPost 객체는 불변성 가정)
        return cls._posts_cache.copy()
    
    @classmethod
    def _get_tags_copy(cls) -> Dict[str, int]:
        """태그 딕셔너리 복사본 반환 - 원본 보호"""
        if cls._tags_cache is None:
            return {}
        
        return cls._tags_cache.copy()
    
    @classmethod
    def _invalidate_posts_cache(cls) -> None:
        """포스트 캐시 무효화"""
        cls._posts_cache = None
        cls._posts_index.clear()
        cls._cache_metadata.pop('posts_cache_time', None)
        cls._cache_metadata.pop('files_hash', None)
    
    @classmethod
    def _invalidate_tags_cache(cls) -> None:
        """태그 캐시 무효화"""
        cls._tags_cache = None
        cls._cache_metadata.pop('tags_cache_time', None)
    
    @classmethod
    def _invalidate_all_cache(cls) -> None:
        """전체 캐시 무효화"""
        cls._posts_cache = None
        cls._tags_cache = None
        cls._posts_index.clear()
        cls._cache_metadata.clear()
    
    @classmethod
    def _calculate_directory_hash(cls, directory: Path) -> str:
        """디렉토리 내 파일들의 해시값 계산 - 정확한 변경 감지"""
        try:
            if not directory.exists():
                return ''
            
            # 텍스트 파일들의 수정 시간과 크기로 해시 생성
            file_info = []
            allowed_extensions = current_app.config.get('ALLOWED_TEXT_EXTENSIONS', {'txt', 'md'})
            
            for ext in allowed_extensions:
                for file_path in directory.glob(f"*.{ext}"):
                    try:
                        stat = file_path.stat()
                        # 파일명, 수정시간, 크기를 조합
                        file_info.append(f"{file_path.name}:{stat.st_mtime:.6f}:{stat.st_size}")
                    except Exception:
                        continue
            
            # 파일 정보를 정렬하여 일관된 해시 생성
            file_info.sort()
            combined_info = '|'.join(file_info)
            
            # SHA256 해시 사용 (MD5보다 안전)
            return hashlib.sha256(combined_info.encode('utf-8')).hexdigest()
            
        except Exception as e:
            current_app.logger.error(f"디렉토리 해시 계산 오류: {e}")
            return str(time.time())  # 오류 시 현재 시간으로 대체
    
    @classmethod
    def _estimate_memory_usage(cls) -> str:
        """캐시 메모리 사용량 추정"""
        try:
            import sys
            
            total_size = 0
            
            # 포스트 캐시 크기
            if cls._posts_cache:
                total_size += sys.getsizeof(cls._posts_cache)
                for post in cls._posts_cache:
                    total_size += sys.getsizeof(post.content)
                    total_size += sys.getsizeof(post.title)
                    total_size += sum(sys.getsizeof(tag) for tag in post.tags)
            
            # 포스트 인덱스 크기
            total_size += sys.getsizeof(cls._posts_index)
            for key in cls._posts_index:
                total_size += sys.getsizeof(key)
            
            # 태그 캐시 크기
            if cls._tags_cache:
                total_size += sys.getsizeof(cls._tags_cache)
                for tag, count in cls._tags_cache.items():
                    total_size += sys.getsizeof(tag) + sys.getsizeof(count)
            
            # 메타데이터 크기
            total_size += sys.getsizeof(cls._cache_metadata)
            
            # 크기 단위 변환
            if total_size < 1024:
                return f"{total_size}B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f}KB"
            else:
                return f"{total_size / (1024 * 1024):.1f}MB"
                
        except Exception:
            return "unknown"


# 전역 캐시 서비스 인스턴스 (옵션)
cache_service = CacheService