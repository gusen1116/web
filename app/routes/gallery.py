# app/routes/gallery.py

from flask import Blueprint, render_template, current_app, abort
from app.services.gallery_service import get_all_photos, get_photo_by_id
from app import cache # 캐시 객체 임포트

gallery_bp = Blueprint('gallery', __name__, url_prefix='/gallery')

@gallery_bp.route('/')
@cache.cached(timeout=300) # 5분 캐싱
def index():
    """갤러리 메인 페이지 - 태그 기반 필터링"""
    try:
        all_photos = get_all_photos()
        all_tags = sorted(list(set(tag for photo in all_photos for tag in photo['tags'])))
        
        return render_template('gallery/index.html', 
                        photos=all_photos, 
                        tags=all_tags)
        
    except Exception as e:
        current_app.logger.error(f'갤러리 인덱스 페이지 오류: {e}', exc_info=True)
        return render_template('gallery/index.html', photos=[], tags=[], error=True)

@gallery_bp.route('/photo/<string:filename>')
@cache.cached(timeout=3600) # 1시간 캐싱
def view_photo(filename):
    """개별 사진 상세 페이지 라우트"""
    try:
        photo = get_photo_by_id(filename)
        if not photo:
            abort(404)
        
        all_photos = get_all_photos() # 캐시된 결과를 사용하게 될 것
        current_index = next((i for i, p in enumerate(all_photos) if p['id'] == filename), -1)
        
        prev_photo = all_photos[current_index + 1] if current_index != -1 and current_index + 1 < len(all_photos) else None
        next_photo = all_photos[current_index - 1] if current_index > 0 else None

        return render_template('gallery/detail.html', 
                            photo=photo,
                            prev_photo=prev_photo,
                            next_photo=next_photo)
    except Exception as e:
        current_app.logger.error(f'사진 상세 페이지 로드 오류: {e}', exc_info=True)
        abort(500)