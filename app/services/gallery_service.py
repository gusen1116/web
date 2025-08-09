import os
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
from flask import current_app, url_for

# Attempt to enable HEIC/HEIF support via pillow‑heif.  If the
# dependency is missing the module gracefully continues without
# support.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_ENABLED = True
except ImportError:
    HEIF_ENABLED = False


def _get_thumbnail_path(filename: str) -> str:
    """Return the absolute path of the thumbnail for ``filename``.

    The function ensures that the thumbnail directory exists before
    returning the path.  It uses the ``gallery_thumbnails`` folder
    inside Flask’s static directory.
    """
    thumb_dir = os.path.join(current_app.static_folder, 'gallery_thumbnails')
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    return os.path.join(thumb_dir, filename)


def _create_thumbnail(image_path: str, thumb_path: str) -> bool:
    """Generate a thumbnail for ``image_path`` and save it to
    ``thumb_path``.

    The thumbnail is limited to 400×400 pixels, preserves aspect ratio
    and uses JPEG format with reasonable quality.  Any errors are
    logged and ``False`` is returned.
    """
    try:
        with Image.open(image_path) as img:
            # Correct orientation using EXIF data
            img = ImageOps.exif_transpose(img)
            img.thumbnail((400, 400))
            img.save(thumb_path, "JPEG", quality=85, optimize=True)
        return True
    except Exception as e:  # pragma: no cover - logging only
        current_app.logger.error(f"썸네일 생성 실패 {os.path.basename(image_path)}: {e}")
        return False


def _get_exif_data(image_path: str) -> dict:
    """Extract EXIF and other metadata from an image.

    Supports JPEG/HEIC/PNG formats.  For PNG, falls back to
    ``image.info`` for basic metadata keys (title, description, author).
    Returns a dictionary keyed by human‑readable EXIF tag names.
    """
    try:
        with Image.open(image_path) as image:
            exif_data: dict = {}
            # 1. Extract EXIF data
            exif_raw = image.getexif()
            if exif_raw:
                for tag_id, value in exif_raw.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value

            # 2. Extract PNG metadata
            if image.format == 'PNG' and image.info:
                for key, value in image.info.items():
                    if key.lower() in ['title', 'description']:
                        exif_data['ImageDescription'] = value
                    elif key.lower() == 'author':
                        exif_data['Artist'] = value
            return exif_data
    except Exception as e:  # pragma: no cover - logging only
        current_app.logger.warning(f"메타데이터 읽기 오류 {os.path.basename(image_path)}: {e}")
        return {}


def _format_exif_value(key: str, value) -> str | None:
    """Format specific EXIF values into a human‑readable string.

    Handles shutter speed (ExposureTime), aperture (FNumber), ISO,
    focal length and byte/tuple formats.  Falls back to ``str``
    representation for unknown types.
    """
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
            # Convert simple numeric tuples to comma‑separated strings
            return ", ".join(map(str, value))
    except (ValueError, TypeError, ZeroDivisionError, IndexError):
        # Fall through to return str(value)
        return str(value)
    return str(value)


def get_all_photos() -> list[dict]:
    """Return metadata for all photos in the configured gallery directory.

    The returned list of dictionaries includes keys: ``id``, ``url``,
    ``thumbnail_url``, ``title``, ``tags`` and ``exif``.  It
    automatically generates thumbnails as needed.
    """
    photos_dir = current_app.config.get('GALLERY_PHOTOS_DIR')
    if not os.path.isdir(photos_dir):
        current_app.logger.error(f"갤러리 디렉토리 없음: {photos_dir}")
        return []

    photo_list: list[dict] = []
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

        # Format and filter EXIF data
        formatted_exif: dict = {}
        for key, value in exif_data.items():
            if key not in ['MakerNote', 'UserComment']:
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


def get_photo_by_id(filename: str) -> dict | None:
    """Return metadata for a single photo identified by ``filename``.

    Returns ``None`` if the photo does not exist.  This function is
    primarily used by the gallery detail route.
    """
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

    # Format and filter EXIF data
    formatted_exif: dict = {}
    for key, value in exif_data.items():
        if key not in ['MakerNote', 'UserComment']:
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