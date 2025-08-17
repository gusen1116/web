import os
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from flask import current_app, url_for

# HEIC/HEIF 지원 (있으면 사용)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_ENABLED = True
except ImportError:
    HEIF_ENABLED = False


def _get_thumbnail_path(filename: str) -> str:
    """static/gallery_thumbnails/<filename> 절대경로 반환 (폴더 없으면 생성)."""
    thumb_dir = os.path.join(current_app.static_folder, 'gallery_thumbnails')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    return os.path.join(thumb_dir, filename)


def _create_thumbnail(image_path: str, thumb_path: str) -> bool:
    """원본에서 400x400 썸네일 생성(JPEG, 품질 85)."""
    try:
        with Image.open(image_path) as img:
            img = ImageOps.exif_transpose(img)  # EXIF 회전 보정
            img.thumbnail((400, 400))
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:  # pragma: no cover
        current_app.logger.error(f"썸네일 생성 실패 {os.path.basename(image_path)}: {e}")
        return False


def _gps_to_deg(value, ref):
    """Pillow EXIF의 (도,분,초) 튜플을 float 도(degree)로 변환."""
    try:
        def _rv(x):
            if isinstance(x, tuple) and len(x) == 2:
                num, den = x
                return num / den if den else 0.0
            return float(x)
        d = _rv(value[0]); m = _rv(value[1]); s = _rv(value[2])
        deg = d + (m / 60.0) + (s / 3600.0)
        if ref in ('S', 'W'):
            deg = -deg
        return round(deg, 7)
    except Exception:
        return None


def _extract_gps(exif: dict) -> dict | None:
    """EXIF dict에서 위/경도를 {'lat':.., 'lon':..}로 추출."""
    gps = exif.get('GPSInfo') or {}
    if not isinstance(gps, dict):
        return None

    lat = gps.get('GPSLatitude');    lat_ref = gps.get('GPSLatitudeRef')
    lon = gps.get('GPSLongitude');   lon_ref = gps.get('GPSLongitudeRef')

    # 숫자 키로 들어오는 경우 보정
    if lat is None and 2 in gps: lat = gps.get(2)
    if lat_ref is None and 1 in gps: lat_ref = gps.get(1)
    if lon is None and 4 in gps: lon = gps.get(4)
    if lon_ref is None and 3 in gps: lon_ref = gps.get(3)

    if not (lat and lon and lat_ref and lon_ref):
        return None

    lat_deg = _gps_to_deg(lat, lat_ref if isinstance(lat_ref, str) else str(lat_ref))
    lon_deg = _gps_to_deg(lon, lon_ref if isinstance(lon_ref, str) else str(lon_ref))
    if lat_deg is None or lon_deg is None:
        return None
    return {'lat': lat_deg, 'lon': lon_deg}


def _get_exif_data(image_path: str) -> dict:
    """이미지에서 EXIF/PNG 메타데이터 추출. 사람이 읽기 좋은 키로 반환."""
    try:
        with Image.open(image_path) as image:
            exif_data: dict = {}
            # 1) EXIF
            exif_raw = image.getexif()
            if exif_raw:
                for tag_id, value in exif_raw.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            # 2) PNG info (제목/설명/작가)
            if image.format == 'PNG' and image.info:
                for key, value in image.info.items():
                    if key.lower() in ['title', 'description']:
                        exif_data['ImageDescription'] = value
                    elif key.lower() == 'author':
                        exif_data['Artist'] = value

            # 3) GPS 좌표 파싱(가능하면)
            gps_point = _extract_gps(exif_data)
            if gps_point:
                exif_data['__GPSPoint'] = gps_point  # 내부 키(가공용)

            return exif_data
    except Exception as e:  # pragma: no cover
        current_app.logger.warning(f"메타데이터 읽기 오류 {os.path.basename(image_path)}: {e}")
        return {}


def _format_exif_value(key: str, value) -> str | None:
    """대표적인 EXIF 값을 보기 좋게 포맷."""
    if value is None or value == '':
        return None
    try:
        if key == 'ExposureTime':
            if isinstance(value, (float, int)) and value > 0:
                return f"1/{int(1/value)}s" if value < 1.0 else f"{int(value)}s"
        elif key == 'FNumber':
            if isinstance(value, tuple):
                return f"f/{value[0]/value[1]:.1f}"
            return f"f/{float(value):.1f}"
        elif key == 'ISOSpeedRatings':
            return f"{value}"
        elif key == 'FocalLength':
            f_val = value[0] / value[1] if isinstance(value, tuple) else value
            return f"{int(f_val)}mm"
        
        # 다른 모든 태그들은 바이트를 문자열로 디코딩
        if isinstance(value, bytes):
            return value.decode('utf-8', 'ignore').strip().strip('\x00')
        
        # 튜플이면 문자열로 join
        if isinstance(value, tuple) and all(isinstance(x, int) for x in value):
            return ", ".join(map(str, value))
            
        return str(value).strip().strip('\x00')

    except (ValueError, TypeError, ZeroDivisionError, IndexError):
        return str(value)


def process_photo_file(filename: str, photos_dir: str) -> dict | None:
    """단일 사진 파일 처리 로직 (공통화)"""
    file_path = os.path.join(photos_dir, filename)
    if not os.path.exists(file_path):
        return None

    thumb_path = _get_thumbnail_path(filename)
    if not os.path.exists(thumb_path):
        _create_thumbnail(file_path, thumb_path)

    exif_data = _get_exif_data(file_path)
    date_taken = exif_data.get('DateTimeOriginal') or exif_data.get('DateTimeDigitized')
    year_tag = date_taken.split(':')[0] if isinstance(date_taken, str) and ':' in date_taken else '날짜정보없음'

    # EXIF 정제
    formatted_exif: dict = {}
    for key, value in exif_data.items():
        # 내부용 키나 불필요한 태그는 건너뜀
        if key in ['MakerNote', 'UserComment', '__GPSPoint', 'ExifOffset', 'ColorSpace', 'ComponentsConfiguration']:
            continue
        formatted_value = _format_exif_value(key, value)
        if formatted_value:
            formatted_exif[key] = formatted_value

    gps_point = exif_data.get('__GPSPoint')

    return {
        'id': filename,
        'url': url_for('static', filename=f'gallery_photos/{filename}'),
        'thumbnail_url': url_for('static', filename=f'gallery_thumbnails/{filename}'),
        'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
        'tags': [year_tag],
        'exif': formatted_exif,
        'gps': gps_point
    }


def get_all_photos() -> list[dict]:
    """설정된 폴더의 사진 메타데이터 목록을 반환."""
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir):
        current_app.logger.error(f"갤러리 디렉토리 없음: {photos_dir}")
        return []

    photo_list: list[dict] = []
    allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

    for filename in sorted(os.listdir(photos_dir), reverse=True):
        if os.path.splitext(filename)[1].lower() not in allowed_ext:
            continue
        
        photo_data = process_photo_file(filename, photos_dir)
        if photo_data:
            photo_list.append(photo_data)
            
    return photo_list


def get_photo_by_id(filename: str) -> dict | None:
    """단일 사진 메타데이터 반환. 없으면 None."""
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    return process_photo_file(filename, photos_dir)