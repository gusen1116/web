import os
from PIL import Image
from PIL.ExifTags import TAGS
from flask import current_app, url_for

def _get_exif_data(image_path):
    try:
        image = Image.open(image_path)
        exif_data_raw = image._getexif()
        if not exif_data_raw:
            return {}
    except Exception as e:
        current_app.logger.warning(f"EXIF 데이터를 읽는 중 오류 발생 {image_path}: {e}")
        return {}
    exif_data = {}
    for tag_id, value in exif_data_raw.items():
        tag = TAGS.get(tag_id, tag_id)
        exif_data[tag] = value
    return exif_data

def _format_exif_value(data, key):
    value = data.get(key)
    if not value:
        return None
    try:
        if key == 'ExposureTime' and isinstance(value, (float, int)) and value > 0:
            return f"1/{int(1/value)}s"
        if key == 'FNumber':
            return f"f/{value}"
        if key == 'ISOSpeedRatings':
            return f"ISO {value}"
        if key == 'FocalLength':
            return f"{int(value)}mm"
    except (ValueError, TypeError):
        return str(value)
    return str(value)

def get_all_photos():
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir):
        current_app.logger.error(f"갤러리 사진 디렉토리를 찾을 수 없습니다: {photos_dir}")
        return []

    photo_list = []
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

    for filename in sorted(os.listdir(photos_dir)):
        if os.path.splitext(filename)[1].lower() not in allowed_extensions:
            continue

        file_path = os.path.join(photos_dir, filename)
        exif_data = _get_exif_data(file_path)

        # 제목은 파일명에서 추출
        parts = os.path.splitext(filename)[0].split('_')
        title = parts[-1].replace('-', ' ').title()

        # 연도 태그 추출
        date_taken = exif_data.get('DateTimeOriginal')
        year_tag = date_taken.split(':')[0] if date_taken else '기타'
        tags = [year_tag]

        photo_info = {
            'id': filename,
            'url': url_for('static', filename=f'gallery_photos/{filename}'),
            'title': title,
            'tags': tags,
            'exif': {
                'camera_model': exif_data.get('Model'),
                'lens_model': exif_data.get('LensModel'),
                'iso': _format_exif_value(exif_data, 'ISOSpeedRatings'),
                'shutter_speed': _format_exif_value(exif_data, 'ExposureTime'),
                'aperture': _format_exif_value(exif_data, 'FNumber'),
                'focal_length': _format_exif_value(exif_data, 'FocalLength'),
                'date_taken': date_taken,
            }
        }
        photo_list.append(photo_info)
    return photo_list[::-1]

def get_photo_by_id(filename):
    all_photos = get_all_photos()
    return next((p for p in all_photos if p['id'] == filename), None)
