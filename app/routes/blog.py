# app/routes/blog.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.post import Post
from app.services.blog_service import create_post, update_post, delete_post

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/posts', methods=['GET'])
def get_posts():
    # 포스트 목록 반환
    pass

@blog_bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    # 특정 포스트 조회
    pass

@blog_bp.route('/posts/new', methods=['GET'])
@login_required
def new_post_form():
    # 새 포스트 작성 폼 반환
    return render_template('blog/editor.html')

@blog_bp.route('/posts', methods=['POST'])
@login_required
def create_new_post():
    # 새 포스트 생성
    data = request.json
    post = create_post(current_user.id, data)
    return jsonify({"success": True, "id": post.id})