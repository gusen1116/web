# app/routes/main_routes.py
from flask import Blueprint, render_template, current_app
from app.services.cache_service import CacheService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """메인 페이지"""
    try:
        # 최근 포스트 3개
        all_posts = CacheService.get_posts_with_cache()
        recent_posts = all_posts[:3] if len(all_posts) >= 3 else all_posts
        
        # 인기 태그
        tags_count = CacheService.get_tags_with_cache()
        popular_tags = sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return render_template(
            'index.html',
            recent_posts=recent_posts,
            popular_tags=popular_tags
        )
        
    except Exception as e:
        current_app.logger.error(f'메인 페이지 로드 에러: {str(e)}')
        return render_template('index.html', recent_posts=[], popular_tags=[])

@main_bp.route('/about')
def about():
    """소개 페이지"""
    return render_template('about.html')