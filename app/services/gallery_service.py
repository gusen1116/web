# app/services/gallery_service.py

import os
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from flask import current_app, url_for

# HEIC/HEIF 포맷 지원 (pip install pillow-heif)
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_ENABLED = True
except ImportError:
    HEIF_ENABLED = False

def _get_thumbnail_path(filename):
    """썸네일 이미지의 전체 경로를 반환합니다."""
    thumb_dir = os.path.join(current_app.static_folder, 'gallery_thumbnails')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    return os.path.join(thumb_dir, filename)

def _create_thumbnail(image_path, thumb_path):
    """썸네일 이미지를 생성하고 저장합니다."""
    try:
        with Image.open(image_path) as img:
            # EXIF 데이터를 기반으로 이미지 회전 보정
            img = ImageOps.exif_transpose(img)
            img.thumbnail((400, 400))
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:
        current_app.logger.error(f"썸네일 생성 실패 {os.path.basename(image_path)}: {e}")
        return False

def _get_exif_data(image_path):
    """다양한 포맷의 이미지에서 메타데이터를 안전하게 추출합니다."""
    try:
        with Image.open(image_path) as image:
            exif_data = {}
            # 1. EXIF 데이터 추출
            exif_raw = image.getexif()
            if exif_raw:
                for tag_id, value in exif_raw.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            # 2. PNG 메타데이터 추출
            if image.format == 'PNG' and image.info:
                for key, value in image.info.items():
                    if key.lower() in ['title', 'description']:
                        exif_data['ImageDescription'] = value
                    elif key.lower() == 'author':
                        exif_data['Artist'] = value
            return exif_data
    except Exception as e:
        current_app.logger.warning(f"메타데이터 읽기 오류 {os.path.basename(image_path)}: {e}")
        return {}

def _format_exif_value(key, value):
    """EXIF 값을 사람이 읽기 좋은 형태로 변환합니다."""
    if not value:
        return None
    try:
        if key == 'ExposureTime':
            if isinstance(value, (float, int)) and value > 0:
                return f"1/{int(1/value)}s" if value < 1.0 else f"{int(value)}s"
        elif key == 'FNumber':
            return f"f/{value}"
        elif key == 'ISOSpeedRatings':
            return f"ISO {value}"
        elif key == 'FocalLength':
            f_val = value[0] / value[1] if isinstance(value, tuple) else value
            return f"{int(f_val)}mm"
        elif isinstance(value, bytes):
            return value.decode('utf-8', 'ignore').strip()
        elif isinstance(value, tuple) and all(isinstance(x, int) for x in value):
             # 간단한 숫자 튜플은 문자열로 변환
            return ", ".join(map(str, value))

    except (ValueError, TypeError, ZeroDivisionError, IndexError):
        return str(value)
    return str(value)


def get_all_photos():
    """모든 사진 정보와 썸네일 URL을 포함하여 반환합니다."""
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir):
        current_app.logger.error(f"갤러리 디렉토리 없음: {photos_dir}")
        return []

    photo_list = []
    allowed_ext = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

    for filename in sorted(os.listdir(photos_dir), reverse=True):
        if os.path.splitext(filename)[1].lower() not in allowed_ext:
            continue

        file_path = os.path.join(photos_dir, filename)
        thumb_path = _get_thumbnail_path(filename)

        if not os.path.exists(thumb_path):
            _create_thumbnail(file_path, thumb_path)

        exif_data = _get_exif_data(file_path)
        date_taken = exif_data.get('DateTimeOriginal') or exif_data.get('DateTimeDigitized')
        year_tag = date_taken.split(':')[0] if date_taken and ':' in date_taken else '날짜정보없음'

        # 모든 EXIF 데이터를 포매팅하여 저장
        formatted_exif = {}
        for key, value in exif_data.items():
            if key not in ['MakerNote', 'UserComment']: # 너무 길거나 깨지는 정보 제외
                 formatted_value = _format_exif_value(key, value)
                 if formatted_value:
                    formatted_exif[key] = formatted_value

        photo_list.append({
            'id': filename,
            'url': url_for('static', filename=f'gallery_photos/{filename}'),
            'thumbnail_url': url_for('static', filename=f'gallery_thumbnails/{filename}'),
            'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
            'tags': [year_tag],
            'exif': formatted_exif
        })
    return photo_list

def get_photo_by_id(filename):
    """파일 이름으로 특정 사진 정보를 찾습니다."""
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    file_path = os.path.join(photos_dir, filename)
    if not os.path.exists(file_path):
        return None

    thumb_path = _get_thumbnail_path(filename)
    if not os.path.exists(thumb_path):
        _create_thumbnail(file_path, thumb_path)

    exif_data = _get_exif_data(file_path)
    date_taken = exif_data.get('DateTimeOriginal') or exif_data.get('DateTimeDigitized')
    year_tag = date_taken.split(':')[0] if date_taken and ':' in date_taken else '날짜정보없음'

    # 모든 EXIF 데이터를 포매팅하여 저장
    formatted_exif = {}
    for key, value in exif_data.items():
        if key not in ['MakerNote', 'UserComment']: # 너무 길거나 깨지는 정보 제외
            formatted_value = _format_exif_value(key, value)
            if formatted_value:
                formatted_exif[key] = formatted_value

    return {
        'id': filename,
        'url': url_for('static', filename=f'gallery_photos/{filename}'),
        'thumbnail_url': url_for('static', filename=f'gallery_thumbnails/{filename}'),
        'title': os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title(),
        'tags': [year_tag],
        'exif': formatted_exif
    }