# app/routes/gallery.py
from flask import Blueprint, render_template, current_app, abort, request
from typing import Dict
import re

# 블루프린트 생성
gallery_bp = Blueprint('gallery', __name__, url_prefix='/gallery')

# 허용된 갤러리 타입 (포트폴리오 카테고리)
ALLOWED_GALLERY_TYPES = {
    'portrait': {
        'template': 'gallery/portrait.html',
        'title': '인물 사진',
        'description': '사람들의 감정과 표정을 담은 인물 사진 컬렉션입니다.'
    },
    'landscape': {
        'template': 'gallery/landscape.html', 
        'title': '풍경 사진',
        'description': '자연의 아름다움과 도시의 풍경을 담은 사진들입니다.'
    },
    'street': {
        'template': 'gallery/street.html',
        'title': '스트리트 포토',
        'description': '일상 속 특별한 순간들을 포착한 거리 사진입니다.'
    },
    'macro': {
        'template': 'gallery/macro.html',
        'title': '매크로 사진',
        'description': '작은 세계의 디테일을 확대해서 담은 근접 사진입니다.'
    }
}

# 안전한 갤러리 타입 패턴
SAFE_GALLERY_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]{1,50}$')


@gallery_bp.route('/')
def index():
    """
    갤러리 메인 페이지 - 포트폴리오 인덱스
    
    주요 구성:
    - 대표 사진 슬라이더/배너
    - 카테고리별 갤러리 그리드
    - 작가 소개 섹션
    """
    try:
        # 사용 가능한 갤러리 목록 생성
        galleries = []
        for gallery_type, gallery_info in ALLOWED_GALLERY_TYPES.items():
            galleries.append({
                'type': gallery_type,
                'title': gallery_info['title'],
                'description': gallery_info['description'],
                'url': f'/gallery/{gallery_type}',
                'thumbnail': f'/static/img/gallery-{gallery_type}.jpg',  # 썸네일 이미지
                'photo_count': 24  # 임시 개수 (나중에 실제 개수로 대체)
            })
        
        return render_template(
            'gallery/index.html',
            galleries=galleries,
            total_galleries=len(galleries)
        )
        
    except Exception as e:
        current_app.logger.error(f'갤러리 인덱스 페이지 오류: {e}')
        return render_template('gallery/index.html', galleries=[], error=True)


@gallery_bp.route('/portrait')
def portrait_gallery():
    """인물 사진 갤러리 페이지"""
    try:
        return render_template(
            'gallery/portrait.html',
            page_title='인물 사진',
            gallery_type='portrait'
        )
    except Exception as e:
        current_app.logger.error(f'인물 갤러리 페이지 오류: {e}')
        abort(500)


@gallery_bp.route('/landscape') 
def landscape_gallery():
    """풍경 사진 갤러리 페이지"""
    try:
        return render_template(
            'gallery/landscape.html',
            page_title='풍경 사진',
            gallery_type='landscape'
        )
    except Exception as e:
        current_app.logger.error(f'풍경 갤러리 페이지 오류: {e}')
        abort(500)


@gallery_bp.route('/street')
def street_gallery():
    """스트리트 포토 갤러리 페이지"""
    try:
        return render_template(
            'gallery/street.html',
            page_title='스트리트 포토',
            gallery_type='street'
        )
    except Exception as e:
        current_app.logger.error(f'스트리트 갤러리 페이지 오류: {e}')
        abort(500)


@gallery_bp.route('/macro')
def macro_gallery():
    """매크로 사진 갤러리 페이지"""
    try:
        return render_template(
            'gallery/macro.html',
            page_title='매크로 사진',
            gallery_type='macro'
        )
    except Exception as e:
        current_app.logger.error(f'매크로 갤러리 페이지 오류: {e}')
        abort(500)


@gallery_bp.route('/<string:gallery_type>')
def dynamic_gallery(gallery_type: str):
    """
    동적 갤러리 라우트 - 보안 강화
    
    Args:
        gallery_type: 갤러리 타입
        
    Returns:
        Response: 해당 갤러리 페이지 또는 404
    """
    try:
        # 입력 검증
        if not gallery_type or not isinstance(gallery_type, str):
            abort(400)
        
        # 보안 패턴 검증
        if not SAFE_GALLERY_PATTERN.match(gallery_type):
            current_app.logger.warning(f'잘못된 갤러리 타입 접근: {gallery_type}')
            abort(400)
        
        # 허용된 갤러리 타입인지 확인
        if gallery_type not in ALLOWED_GALLERY_TYPES:
            current_app.logger.info(f'존재하지 않는 갤러리 타입: {gallery_type}')
            abort(404)
        
        # 정적 라우트와 중복 방지
        static_routes = ['portrait', 'landscape', 'street', 'macro']
        if gallery_type in static_routes:
            # 해당 정적 라우트로 리다이렉트
            from flask import redirect, url_for
            return redirect(url_for(f'gallery.{gallery_type}_gallery'))
        
        # 갤러리 정보 가져오기
        gallery_info = ALLOWED_GALLERY_TYPES[gallery_type]
        
        # 템플릿 렌더링
        return render_template(
            gallery_info['template'],
            page_title=gallery_info['title'],
            gallery_type=gallery_type,
            description=gallery_info['description']
        )
        
    except Exception as e:
        current_app.logger.error(f'동적 갤러리 라우트 오류 {gallery_type}: {e}')
        abort(500)


@gallery_bp.route('/api/<gallery_type>/config')
def api_gallery_config(gallery_type: str):
    """
    갤러리 설정 API - 클라이언트용 설정 정보 제공
    
    Args:
        gallery_type: 갤러리 타입
        
    Returns:
        JSON: 갤러리 설정 정보
    """
    try:
        # 입력 검증
        if not SAFE_GALLERY_PATTERN.match(gallery_type):
            return {'error': '잘못된 갤러리 타입'}, 400
        
        if gallery_type not in ALLOWED_GALLERY_TYPES:
            return {'error': '지원하지 않는 갤러리'}, 404
        
        # 갤러리별 기본 설정
        configs = {
            'portrait': {
                'layout': 'grid',
                'thumbnail_size': 'medium',
                'lightbox_enabled': True,
                'metadata_display': ['camera', 'lens', 'date', 'location'],
                'sorting': 'date_desc'
            },
            'landscape': {
                'layout': 'masonry',
                'thumbnail_size': 'large',
                'lightbox_enabled': True,
                'metadata_display': ['camera', 'date', 'location', 'weather'],
                'sorting': 'date_desc'
            },
            'street': {
                'layout': 'timeline',
                'thumbnail_size': 'medium',
                'lightbox_enabled': True,
                'metadata_display': ['camera', 'date', 'location'],
                'sorting': 'date_desc'
            },
            'macro': {
                'layout': 'grid',
                'thumbnail_size': 'square',
                'lightbox_enabled': True,
                'metadata_display': ['camera', 'lens', 'magnification', 'date'],
                'sorting': 'date_desc'
            }
        }
        
        config = configs.get(gallery_type, {})
        
        return {
            'type': gallery_type,
            'title': ALLOWED_GALLERY_TYPES[gallery_type]['title'],
            'config': config,
            'version': '1.0'
        }
        
    except Exception as e:
        current_app.logger.error(f'갤러리 설정 API 오류: {e}')
        return {'error': '서버 오류'}, 500


@gallery_bp.route('/api/list')
def api_gallery_list():
    """
    사용 가능한 갤러리 목록 API
    
    Returns:
        JSON: 갤러리 목록
    """
    try:
        galleries = []
        
        for gallery_type, gallery_info in ALLOWED_GALLERY_TYPES.items():
            galleries.append({
                'type': gallery_type,
                'title': gallery_info['title'],
                'description': gallery_info['description'],
                'url': f'/gallery/{gallery_type}',
                'api_config_url': f'/gallery/api/{gallery_type}/config'
            })
        
        return {
            'galleries': galleries,
            'total': len(galleries),
            'version': '1.0'
        }
        
    except Exception as e:
        current_app.logger.error(f'갤러리 목록 API 오류: {e}')
        return {'error': '서버 오류'}, 500


# ===== 에러 핸들러 =====

@gallery_bp.errorhandler(400)
def bad_request_handler(error):
    """400 에러 핸들러"""
    return render_template('400.html', error=error), 400


@gallery_bp.errorhandler(404) 
def not_found_handler(error):
    """404 에러 핸들러 - 갤러리 전용"""
    current_app.logger.info(f'갤러리 404: {request.url}')
    
    # 사용 가능한 갤러리 목록과 함께 404 페이지 표시
    try:
        available_galleries = list(ALLOWED_GALLERY_TYPES.keys())
        return render_template(
            '404.html', 
            error=error,
            available_galleries=available_galleries,
            gallery_context=True
        ), 404
    except Exception:
        return render_template('404.html', error=error), 404


@gallery_bp.errorhandler(500)
def internal_error_handler(error):
    """500 에러 핸들러"""
    return render_template('500.html', error=error), 500