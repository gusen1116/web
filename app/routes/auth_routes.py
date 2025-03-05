from flask import Blueprint, render_template

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/')
def index():
    return render_template('blog/index.html')

@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    return render_template('blog/post.html', post_id=post_id)