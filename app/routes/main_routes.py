from flask import Blueprint, render_template
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from sqlalchemy import func
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # 최근 게시물 3개 불러오기
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    
    # 인기 카테고리 (게시물 수 기준)
    popular_categories = db.session.query(
        Category, func.count(Post.id).label('post_count')
    ).join(Post, Category.id == Post.category_id, isouter=True)\
     .group_by(Category.id)\
     .order_by(func.count(Post.id).desc())\
     .limit(5).all()
    
    # 인기 태그 (게시물 수 기준)
    popular_tags = db.session.query(
        Tag, func.count(Post.id).label('post_count')
    ).join(Tag.posts)\
     .group_by(Tag.id)\
     .order_by(func.count(Post.id).desc())\
     .limit(10).all()
    
    return render_template('index.html', 
                        recent_posts=recent_posts,
                        popular_categories=popular_categories,
                        popular_tags=popular_tags)

@main_bp.route('/about')
def about():
    return render_template('about.html')