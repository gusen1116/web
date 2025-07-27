# app/services/gallery_service.py
import os
from PIL import Image
from PIL.ExifTags import TAGS
from flask import current_app, url_for

def _get_exif_data(image_path):
    """이미지 파일에서 EXIF 데이터를 추출하고 정리합니다."""
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
    """특정 EXIF 값을 사람이 읽기 좋은 형태로 변환합니다."""
    value = data.get(key)
    if not value:
        return None

    try:
        if key == 'ExposureTime':
            if isinstance(value, (float, int)) and value > 0:
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
    """갤러리 폴더에서 모든 사진과 메타데이터를 불러옵니다."""
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

        parts = os.path.splitext(filename)[0].split('_')
        tags = parts[:-1] if len(parts) > 1 else []
        title = parts[-1].replace('-', ' ').title()

        photo_info = {
            'id': filename,
            'url': url_for('static', filename=f'gallery_photos/{filename}'),
            'title': title,
            'tags': tags or ['기타'],
            'exif': {
                'camera_model': exif_data.get('Model'),
                'lens_model': exif_data.get('LensModel'),
                'iso': _format_exif_value(exif_data, 'ISOSpeedRatings'),
                'shutter_speed': _format_exif_value(exif_data, 'ExposureTime'),
                'aperture': _format_exif_value(exif_data, 'FNumber'),
                'focal_length': _format_exif_value(exif_data, 'FocalLength'),
                'date_taken': exif_data.get('DateTimeOriginal'),
            }
        }
        photo_list.append(photo_info)
    
    return photo_list[::-1]

# --- ▼▼▼▼▼ 오류 해결을 위해 이 함수를 추가합니다. ▼▼▼▼▼ ---
def get_photo_by_id(filename):
    """파일 이름으로 특정 사진 한 장의 정보를 찾습니다."""
    # 전체 사진 목록을 가져와서 일치하는 id(filename)를 가진 사진을 찾습니다.
    all_photos = get_all_photos()
    return next((p for p in all_photos if p['id'] == filename), None)
# --- ▲▲▲▲▲ 여기까지 추가 ▲▲▲▲▲ ---
