# app/services/gallery_service.py
import os
import json
import requests
import time
import threading
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
from PIL.ExifTags import TAGS
from flask import current_app, url_for

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

def _get_gps_cache_path(): return str(_get_cache_dir() / 'gps_address_cache.json')
def _get_photo_cache_path(): return str(_get_cache_dir() / 'photo_metadata_cache.json')

_address_cache = {}
_photo_cache = {}
_last_api_call = 0
_warmer_thread = None
_warmer_lock = threading.Lock()

def _load_caches():
    global _address_cache, _photo_cache
    gps_path = _get_gps_cache_path()
    photo_path = _get_photo_cache_path()

    if not _address_cache:
        try:
            if os.path.exists(gps_path):
                with open(gps_path, 'r', encoding='utf-8') as f:
                    _address_cache = json.load(f)
                current_app.logger.info(f"[Gallery] GPS 캐시 로드 완료: {len(_address_cache)} 항목")
        except Exception as e:
            current_app.logger.error(f"[Gallery] GPS 캐시 로드 실패: {e}")
    
    if not _photo_cache:
        try:
            if os.path.exists(photo_path):
                with open(photo_path, 'r', encoding='utf-8') as f:
                    _photo_cache = json.load(f)
                current_app.logger.info(f"[Gallery] 메타데이터 캐시 로드 완료: {len(_photo_cache)} 항목")
        except Exception as e:
            current_app.logger.error(f"[Gallery] 메타데이터 캐시 로드 실패: {e}")

def _save_gps_cache():
    path = _get_gps_cache_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_address_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        current_app.logger.error(f"[Gallery] GPS 캐시 저장 실패: {e}")

def _save_photo_cache():
    path = _get_photo_cache_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_photo_cache, f, ensure_ascii=False, indent=2)
        if os.path.exists(path):
            current_app.logger.info(f"[Gallery] 메타데이터 캐시 저장 완료 ({os.path.getsize(path)} bytes)")
    except Exception as e:
        current_app.logger.error(f"[Gallery] 메타데이터 캐시 저장 실패: {e}")

def _background_address_warmer(app_context):
    """백그라운드에서 누락된 주소 정보를 채움 (Nominatim API 정책 준수)"""
    global _last_api_call
    with app_context:
        _load_caches()
        targets = []
        for key, data in _photo_cache.items():
            gps = data.get('gps')
            if gps and gps.get('lat') and not gps.get('address'):
                targets.append((key, gps['lat'], gps['lon']))
        
        if not targets:
            current_app.logger.info("[Gallery] 백그라운드 워머: 업데이트할 주소가 없습니다.")
            return

        current_app.logger.info(f"[Gallery] 백그라운드 워머 시작: {len(targets)}개의 주소 조회 예정")
        for key, lat, lon in targets:
            addr = _get_address(lat, lon, allow_network=True)
            if addr:
                with _warmer_lock:
                    if key in _photo_cache:
                        _photo_cache[key]['gps']['address'] = addr
                _save_photo_cache()
                current_app.logger.info(f"[Gallery] 백그라운드 주소 획득: {key} -> {addr}")
            time.sleep(1.2) # 1.1초 이상 대기 필수
        current_app.logger.info("[Gallery] 백그라운드 워머 종료")

def _start_warmer():
    global _warmer_thread
    if _warmer_thread and _warmer_thread.is_alive(): return
    from flask import current_app
    current_app.logger.info("[Gallery] 백그라운드 워머 스레드 가동...")
    _warmer_thread = threading.Thread(
        target=_background_address_warmer, 
        args=(current_app.app_context(),),
        daemon=True
    )
    _warmer_thread.start()

def _get_thumbnail_filename(filename: str) -> str:
    base, _ = os.path.splitext(filename)
    return f"{base}.jpg"

def _get_thumbnail_path(filename: str) -> str:
    thumb_dir = os.path.join(current_app.static_folder, 'gallery_thumbnails')
    os.makedirs(thumb_dir, exist_ok=True)
    return os.path.join(thumb_dir, _get_thumbnail_filename(filename))

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

def _gps_to_deg(value, ref):
    try:
        def _rv(x):
            if hasattr(x, 'numerator') and hasattr(x, 'denominator'):
                return float(x.numerator) / float(x.denominator) if x.denominator != 0 else 0.0
            return float(x)
        d, m, s = _rv(value[0]), _rv(value[1]), _rv(value[2])
        deg = d + (m / 60.0) + (s / 3600.0)
        return -deg if ref in ('S', 'W') else deg
    except Exception: return None

def _get_address(lat, lon, allow_network=False):
    global _last_api_call
    _load_caches()
    key = f"{lat:.4f},{lon:.4f}"
    if key in _address_cache:
        return _address_cache[key]
    
    if not allow_network: return None
    
    now = time.time()
    if now - _last_api_call < 1.1: return None

    try:
        _last_api_call = now
        headers = {'User-Agent': 'GusenGallery/3.0 (contact: admin@wagusen.com)'}
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}&zoom=12&accept-language=ko"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            addr = data.get('address', {})
            place = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county') or addr.get('province') or addr.get('state') or addr.get('country')
            if place:
                _address_cache[key] = place
                _save_gps_cache()
                return place
    except Exception as e:
        current_app.logger.error(f"[Gallery] 주소 API 호출 실패: {e}")
    return None

def _extract_gps(exif: dict, allow_network=False) -> dict | None:
    gps = exif.get('GPSInfo') or {}
    if not isinstance(gps, dict): return None

    lat = gps.get(2) or gps.get('GPSLatitude')
    lat_ref = gps.get(1) or gps.get('GPSLatitudeRef')
    lon = gps.get(4) or gps.get('GPSLongitude')
    lon_ref = gps.get(3) or gps.get('GPSLongitudeRef')

    if not (lat and lon and lat_ref and lon_ref): return None

    lat_deg = _gps_to_deg(lat, str(lat_ref))
    lon_deg = _gps_to_deg(lon, str(lon_ref))
    if lat_deg is None or lon_deg is None: return None
        
    address = _get_address(lat_deg, lon_deg, allow_network=allow_network)
    return {
        'lat': lat_deg, 'lon': lon_deg, 'address': address,
        'map_url': f"https://www.openstreetmap.org/?mlat={lat_deg}&mlon={lon_deg}#map=15/{lat_deg}/{lon_deg}"
    }

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

            gps_sub = exif_raw.get_ifd(0x8825)
            if gps_sub: exif_data['GPSInfo'] = dict(gps_sub)

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

def process_photo_file(filename: str, photos_dir: str, allow_network=False) -> dict | None:
    file_path = os.path.join(photos_dir, filename)
    if not os.path.exists(file_path): return None

    _load_caches()
    # 캐시 키에 정수형 mtime 사용
    mtime = int(os.path.getmtime(file_path))
    cache_key = f"{filename}_{mtime}"
    
    if cache_key in _photo_cache:
        data = _photo_cache[cache_key].copy()
        # 주소가 필요한데 캐시에 없다면 실시간 조회 시도 (상세 페이지인 경우)
        if data.get('gps') and not data['gps'].get('address') and allow_network:
            addr = _get_address(data['gps']['lat'], data['gps']['lon'], allow_network=True)
            if addr:
                current_app.logger.info(f"[Gallery] 실시간 주소 획득: {filename} -> {addr}")
                data['gps']['address'] = addr
                with _warmer_lock:
                    _photo_cache[cache_key]['gps']['address'] = addr
                _save_photo_cache()
        return data

    current_app.logger.info(f"[Gallery] 캐시 미스 또는 정보 없음 - 재처리: {filename}")
    thumb_path = _get_thumbnail_path(filename)
    # 화질 개선을 위해 기존 썸네일이 있더라도 다시 생성하고 싶다면 아래 조건을 수정할 수 있습니다.
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

    gps_point = _extract_gps(exif_data, allow_network=allow_network)
    
    photo_data = {
        'id': filename,
        'url': url_for('static', filename=f'gallery_photos/{filename}'),
        'thumbnail_url': url_for('static', filename=f'gallery_thumbnails/{_get_thumbnail_filename(filename)}'),
        'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
        'tags': [year_tag],
        'exif_low': exif_low,
        'gps': gps_point
    }
    
    current_app.logger.debug(f"[Gallery] {filename} 파싱 결과: EXIF 키 {list(exif_low.keys())}")
    with _warmer_lock:
        _photo_cache[cache_key] = photo_data
    _save_photo_cache()
    
    return photo_data

def get_all_photos() -> list[dict]:
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir): 
        current_app.logger.error(f"[Gallery] 사진 디렉토리 경로 오류: {photos_dir}")
        return []
    
    photo_list = []
    allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}
    
    filenames = sorted([f for f in os.listdir(photos_dir) 
                        if os.path.splitext(f)[1].lower() in allowed_ext], reverse=True)
    
    current_app.logger.info(f"[Gallery] 사진 목록 로드 시작 (파일수: {len(filenames)})")
    
    needs_warming = False
    for filename in filenames:
        # 목록 로드 시에는 네트워크 요청 없이 캐시만 사용
        photo_data = process_photo_file(filename, photos_dir, allow_network=False)
        if photo_data:
            photo_list.append(photo_data)
            if photo_data.get('gps') and not photo_data['gps'].get('address'):
                needs_warming = True
        
    if needs_warming:
        _start_warmer()
        
    return photo_list

def get_photo_by_id(filename: str) -> dict | None:
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    current_app.logger.info(f"[Gallery] 개별 사진 상세 요청: {filename}")
    return process_photo_file(filename, photos_dir, allow_network=True)
