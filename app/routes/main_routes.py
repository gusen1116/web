from flask import Blueprint, render_template, current_app
import os
from app.services.text_service import get_all_text_posts, get_tags_count

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    text_dir = os.path.join(current_app.instance_path, 'uploads', 'texts')
    
    # 최근 게시물 3개 불러오기
    all_posts = get_all_text_posts(text_dir)
    recent_posts = all_posts[:3] if len(all_posts) >= 3 else all_posts
    
    # 인기 태그 (게시물 수 기준)
    tags_count = get_tags_count(text_dir)
    popular_tags = [(tag, count) for tag, count in tags_count.items()]
    popular_tags.sort(key=lambda x: x[1], reverse=True)
    popular_tags = popular_tags[:10]
    
    return render_template('index.html', 
                        recent_posts=recent_posts,
                        popular_tags=popular_tags)

@main_bp.route('/about')
def about():
    return render_template('about.html')