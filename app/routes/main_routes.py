from flask import Blueprint, render_template
from app.models.post import Post  # Post 모델 import 추가

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    return render_template('index.html', recent_posts=recent_posts)

@main_bp.route('/about')
def about():
    return render_template('about.html')