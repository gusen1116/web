"""
app/routes/gallery.py
----------------------

Routes for the photo gallery. The ``gallery_bp`` blueprint exposes an index
page listing all photos and a detail view for individual photos. Cached
responses are used to improve performance. A bug in the original route
definitions (extraneous whitespace and missing path parameters) has been
fixed by explicitly declaring the filename parameter in the route.
"""

from flask import Blueprint, render_template, current_app, abort
from app.services.gallery_service import get_all_photos, get_photo_by_id
from app import cache

gallery_bp = Blueprint('gallery', __name__, url_prefix='/gallery')

@gallery_bp.route('/')
@cache.cached(timeout=300)
def index():
    """Render the gallery index showing all photos and their tags."""
    try:
        all_photos = get_all_photos()
        all_tags = sorted({tag for photo in all_photos for tag in photo['tags']})
        return render_template('gallery/index.html', photos=all_photos, tags=all_tags)
    except Exception as e:
        current_app.logger.error(f'갤러리 인덱스 페이지 오류: {e}', exc_info=True)
        return render_template('gallery/index.html', photos=[], tags=[], error=True)

@gallery_bp.route('/photo/<filename>')
@cache.cached(timeout=3600)
def view_photo(filename: str):
    """Render a detail page for a single photo identified by its filename."""
    try:
        photo = get_photo_by_id(filename)
        if not photo:
            abort(404)
        all_photos = get_all_photos()
        current_index = next((i for i, p in enumerate(all_photos) if p['id'] == filename), -1)
        prev_photo = all_photos[current_index + 1] if current_index != -1 and current_index + 1 < len(all_photos) else None
        next_photo = all_photos[current_index - 1] if current_index > 0 else None
        return render_template(
            'gallery/detail.html',
            photo=photo,
            prev_photo=prev_photo,
            next_photo=next_photo
        )
    except Exception as e:
        current_app.logger.error(f'사진 상세 페이지 로드 오류: {e}', exc_info=True)
        abort(500)