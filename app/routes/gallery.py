# app/routes/gallery.py
from flask import Blueprint, render_template, current_app, abort
# get_photo_by_id 함수를 새로 import 합니다.
from app.services.gallery_service import get_all_photos, get_photo_by_id

gallery_bp = Blueprint('gallery', __name__, url_prefix='/gallery')

@gallery_bp.route('/')
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

# --- ▼▼▼▼▼ 새로운 라우트 추가 ▼▼▼▼▼ ---
@gallery_bp.route('/photo/<string:filename>')
def view_photo(filename):
    """개별 사진 상세 페이지 라우트"""
    try:
        photo = get_photo_by_id(filename)
        if not photo:
            abort(404)
        
        # 전체 사진 목록에서 현재 사진의 이전/다음 사진 찾기 (네비게이션용)
        all_photos = get_all_photos()
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
# --- ▲▲▲▲▲ 여기까지 추가 ▲▲▲▲▲ ---


@gallery_bp.errorhandler(404) 
def not_found_handler(error):
    # 404 에러 발생 시 메인 갤러리 페이지로 리디렉션하거나 전용 404 템플릿을 보여줄 수 있습니다.
    # 여기서는 간단하게 텍스트를 반환합니다.
    return "사진을 찾을 수 없습니다.", 404
