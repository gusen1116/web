# app/services/gallery_service.py
import os
import json
import threading
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from PIL.ExifTags import TAGS
from flask import current_app, url_for

ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

# HEIC/HEIF 지원
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_ENABLED = True
except ImportError:
    HEIF_ENABLED = False

# 캐시 파일 경로 (쓰기 권한이 확실한 썸네일 디렉토리 활용)
def _get_cache_dir():
    try:
        path = Path(current_app.static_folder) / 'gallery_thumbnails'
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        # Fallback: 현재 디렉토리
        return Path('.')

def _get_photo_cache_path(): return str(_get_cache_dir() / 'photo_metadata_cache.json')

_photo_cache = {}
_cache_lock = threading.Lock()

def _load_caches():
    global _photo_cache
    photo_path = _get_photo_cache_path()

    if not _photo_cache:
        try:
            if os.path.exists(photo_path):
                with open(photo_path, 'r', encoding='utf-8') as f:
                    _photo_cache = json.load(f)
                removed_private_data = False
                for cached_photo in _photo_cache.values():
                    if isinstance(cached_photo, dict) and 'gps' in cached_photo:
                        cached_photo.pop('gps', None)
                        removed_private_data = True
                if removed_private_data:
                    _save_photo_cache()
                current_app.logger.info(f"[Gallery] 메타데이터 캐시 로드 완료: {len(_photo_cache)} 항목")
        except Exception as e:
            current_app.logger.error(f"[Gallery] 메타데이터 캐시 로드 실패: {e}")

def _save_photo_cache():
    path = _get_photo_cache_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_photo_cache, f, ensure_ascii=False, indent=2)
        if os.path.exists(path):
            current_app.logger.info(f"[Gallery] 메타데이터 캐시 저장 완료 ({os.path.getsize(path)} bytes)")
    except Exception as e:
        current_app.logger.error(f"[Gallery] 메타데이터 캐시 저장 실패: {e}")

def is_safe_photo_filename(filename: str) -> bool:
    """Return whether *filename* identifies one top-level gallery image."""
    if not isinstance(filename, str) or not filename or '\x00' in filename:
        return False
    if '/' in filename or '\\' in filename or filename in {'.', '..'}:
        return False
    path = Path(filename)
    return (
        not path.is_absolute()
        and path.name == filename
        and path.suffix.lower() in ALLOWED_PHOTO_EXTENSIONS
    )

def _resolve_photo_path(filename: str, photos_dir: str | os.PathLike | None) -> Path | None:
    """Resolve a gallery image without permitting traversal or escaping symlinks."""
    if not photos_dir or not is_safe_photo_filename(filename):
        return None
    try:
        gallery_root = Path(photos_dir).resolve()
        candidate = (gallery_root / filename).resolve()
        candidate.relative_to(gallery_root)
    except (OSError, RuntimeError, ValueError):
        return None
    return candidate if candidate.is_file() else None

def _get_thumbnail_filename(filename: str) -> str:
    if not is_safe_photo_filename(filename):
        raise ValueError('Unsafe gallery filename')
    base, _ = os.path.splitext(filename)
    return f"{base}.jpg"

def _get_thumbnail_path(filename: str) -> str:
    static_root = Path(current_app.static_folder).resolve()
    thumb_dir = static_root / 'gallery_thumbnails'
    thumb_dir.mkdir(parents=True, exist_ok=True)
    resolved_thumb_dir = thumb_dir.resolve()
    thumb_path = (resolved_thumb_dir / _get_thumbnail_filename(filename)).resolve()
    try:
        resolved_thumb_dir.relative_to(static_root)
        thumb_path.relative_to(resolved_thumb_dir)
    except ValueError as exc:
        raise ValueError('Thumbnail path escaped its configured directory') from exc
    return str(thumb_path)

def _create_thumbnail(image_path: str, thumb_path: str) -> bool:
    """고화질 최적화 썸네일 생성"""
    try:
        with Image.open(image_path) as img:
            # 1. EXIF 회전 정보 반영
            img = ImageOps.exif_transpose(img)
            
            # RGBA인 경우 RGB로 변환 (JPEG 저장용)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 2. 고품질 LANCZOS 필터 사용 및 해상도 800px로 상향 (Retina 대응)
            # 400px보다 4배 선명한 데이터를 확보합니다.
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # 3. 미세 샤프닝으로 선명도 보정 (리사이징 시 발생하는 블러 제거)
            img = img.filter(ImageFilter.SHARPEN)
            
            # 4. 고퀄리티 저장 (Progressive 적용으로 웹 로딩 최적화)
            img.save(thumb_path, "JPEG", quality=90, optimize=True, progressive=True)
            
        return True
    except Exception as e:
        current_app.logger.warning(f"[Gallery] 썸네일 생성 실패 ({image_path}): {e}")
        return False

def _get_exif_data(image_path: str) -> dict:
    try:
        with Image.open(image_path) as image:
            exif_data = {}
            exif_raw = image.getexif()
            if not exif_raw: return {}

            for tag_id, value in exif_raw.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = value

            exif_sub = exif_raw.get_ifd(0x8769)
            if exif_sub:
                for tag_id, value in exif_sub.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            return exif_data
    except Exception as e:
        current_app.logger.error(f"[Gallery] EXIF 읽기 실패 ({image_path}): {e}")
        return {}

def _format_exif_value(key: str, value) -> str | None:
    if value is None or value == '' or str(value).lower() in ('none', 'undefined'): return None
    
    def _to_float(v):
        try:
            if hasattr(v, 'numerator') and hasattr(v, 'denominator'):
                return float(v.numerator) / float(v.denominator) if v.denominator != 0 else 0.0
            return float(v)
        except: return 0.0

    try:
        if key in ('ExposureTime', 'ShutterSpeedValue'):
            f_val = _to_float(value)
            if f_val <= 0: return None
            if f_val < 1.0:
                inv = round(1.0 / f_val)
                return f"1/{inv}s"
            return f"{round(f_val, 1)}s"
        
        elif key in ('FNumber', 'ApertureValue'):
            f_val = _to_float(value)
            return f"f/{f_val:.1f}" if f_val > 0 else None
        
        elif key == 'FocalLength':
            f_val = _to_float(value)
            return f"{f_val:.1f}mm" if f_val > 0 else None
        
        elif key == 'ISOSpeedRatings':
            return str(value)

        if isinstance(value, bytes):
            res = value.decode('utf-8', 'ignore').strip().strip('\x00')
        else:
            res = str(value).strip().strip('\x00')
            
        return res if res.lower() not in ('none', 'undefined', '') else None
    except Exception: return None

def process_photo_file(filename: str, photos_dir: str) -> dict | None:
    resolved_file_path = _resolve_photo_path(filename, photos_dir)
    if resolved_file_path is None:
        current_app.logger.warning(f"[Gallery] 안전하지 않거나 존재하지 않는 사진 경로 거부: {filename!r}")
        return None
    file_path = str(resolved_file_path)

    _load_caches()
    mtime = int(os.path.getmtime(file_path))
    cache_key = f"{filename}_{mtime}"
    
    if cache_key in _photo_cache:
        data = _photo_cache[cache_key].copy()
        data.pop('gps', None)
        return data

    current_app.logger.info(f"[Gallery] 캐시 미스 또는 정보 없음 - 재처리: {filename}")
    thumb_path = _get_thumbnail_path(filename)
    if not os.path.exists(thumb_path): _create_thumbnail(file_path, thumb_path)

    exif_data = _get_exif_data(file_path)
    
    if 'ExposureTime' not in exif_data and 'ShutterSpeedValue' in exif_data:
        try:
            val = exif_data['ShutterSpeedValue']
            if hasattr(val, 'numerator'): val = float(val.numerator)/val.denominator
            exif_data['ExposureTime'] = 1.0 / (2**val)
        except: pass

    date_taken = exif_data.get('DateTimeOriginal') or exif_data.get('DateTimeDigitized')
    year_tag = str(date_taken).split(':')[0] if date_taken else '날짜정보없음'

    exif_low = {}
    mapping = {
        'Model': 'model',
        'FNumber': 'fnumber',
        'ExposureTime': 'exposuretime',
        'ISOSpeedRatings': 'isospeedratings',
        'FocalLength': 'focallength'
    }
    
    for exif_key, target_key in mapping.items():
        val = _format_exif_value(exif_key, exif_data.get(exif_key))
        if val: exif_low[target_key] = val

    photo_data = {
        'id': filename,
        'url': url_for('static', filename=f'gallery_photos/{filename}'),
        'thumbnail_url': url_for('static', filename=f'gallery_thumbnails/{_get_thumbnail_filename(filename)}'),
        'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
        'year': year_tag,
        'tags': [year_tag],
        'exif_low': exif_low
    }
    
    current_app.logger.debug(f"[Gallery] {filename} 파싱 결과: EXIF 키 {list(exif_low.keys())}")
    with _cache_lock:
        _photo_cache[cache_key] = photo_data
    _save_photo_cache()
    
    return photo_data

def get_all_photos() -> list[dict]:
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir): 
        current_app.logger.error(f"[Gallery] 사진 디렉토리 경로 오류: {photos_dir}")
        return []
    
    photo_list = []
    filenames = sorted([f for f in os.listdir(photos_dir) 
                        if os.path.splitext(f)[1].lower() in ALLOWED_PHOTO_EXTENSIONS], reverse=True)
    
    current_app.logger.info(f"[Gallery] 사진 목록 로드 시작 (파일수: {len(filenames)})")
    
    for filename in filenames:
        photo_data = process_photo_file(filename, photos_dir)
        if photo_data:
            photo_list.append(photo_data)
        
    return photo_list

def get_photo_by_id(filename: str) -> dict | None:
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    current_app.logger.info(f"[Gallery] 개별 사진 상세 요청: {filename}")
    return process_photo_file(filename, photos_dir)
