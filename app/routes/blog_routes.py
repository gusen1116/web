# app/routes/blog_routes.py
from flask import Blueprint, render_template, request, jsonify, url_for, redirect, abort, flash
from flask_login import login_required, current_user
from app import db
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.models.post_tag import PostTag
from werkzeug.utils import secure_filename
import os
import json
import time
from datetime import datetime

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

# 파일 업로드 설정
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """파일 확장자 확인"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 블로그 목록
@blog_bp.route('/')
def index():
    """블로그 포스트 목록 페이지"""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('blog/index.html', posts=posts)

# 검색 결과 페이지
@blog_bp.route('/search')
def search():
    """블로그 검색 결과"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('blog.index'))
    
    # 제목 또는 내용에서 검색
    search_term = f"%{query}%"
    posts = Post.query.filter(
        (Post.title.like(search_term)) | 
        (Post.content.like(search_term))
    ).order_by(Post.created_at.desc()).all()
    
    return render_template('blog/search.html', query=query, results=posts)

# 새 글 작성 페이지
@blog_bp.route('/new')
@login_required
def new():
    """새 블로그 포스트 작성 페이지"""
    return render_template('blog/editor.html')

# 포스트 저장 (API)
@blog_bp.route('/posts', methods=['POST'])
@login_required
def create():
    """새 포스트 저장 API"""
    try:
        data = request.json
        
        new_post = Post(
            title=data['title'],
            content=json.dumps(data['content']),
            user_id=current_user.id
        )
        
        # 카테고리 처리 (필요시)
        if 'category' in data and data['category']:
            from app.models.category import Category
            category = Category.query.filter_by(name=data['category']).first()
            if not category:
                category = Category(name=data['category'])
                db.session.add(category)
                db.session.flush()  # ID 생성을 위해 플러시
            new_post.category_id = category.id
        
        # 먼저 포스트 저장
        db.session.add(new_post)
        db.session.flush()  # ID 생성을 위해 플러시
        
        # 태그 처리 (필요시)
        if 'tags' in data and data['tags']:
            from app.models.tag import Tag
            from app.models.post_tag import PostTag
            
            for tag_name in data['tags']:
                if not tag_name:
                    continue
                
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()  # ID 생성을 위해 플러시
                
                post_tag = PostTag(post_id=new_post.id, tag_id=tag.id)
                db.session.add(post_tag)
        
        db.session.commit()
        
        return jsonify({'success': True, 'id': new_post.id})
    
    except Exception as e:
        db.session.rollback()
        print(f"오류: {str(e)}")
        return jsonify({'success': False, 'message': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

# 포스트 상세보기
@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    """블로그 포스트 상세 페이지"""
    post = Post.query.get_or_404(post_id)
    return render_template('blog/post.html', post=post)

# 포스트 수정 페이지
@blog_bp.route('/post/<int:post_id>/edit')
@login_required
def edit(post_id):
    """블로그 포스트 수정 페이지"""
    post = Post.query.get_or_404(post_id)
    
    # 작성자만 수정 가능
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    return render_template('blog/editor.html', post=post)

# 포스트 수정 저장 (API)
@blog_bp.route('/posts/<int:post_id>', methods=['PUT'])
@login_required
def update(post_id):
    """블로그 포스트 수정 API"""
    try:
        post = Post.query.get_or_404(post_id)
        
        if post.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        
        data = request.json
        
        post.title = data['title']
        post.content = json.dumps(data['content'])
        post.updated_at = datetime.utcnow()
        
        # 카테고리 처리 (필요시)
        if 'category' in data and data['category']:
            from app.models.category import Category
            category = Category.query.filter_by(name=data['category']).first()
            if not category:
                category = Category(name=data['category'])
                db.session.add(category)
                db.session.flush()  # ID 생성을 위해 플러시
            post.category_id = category.id
        else:
            post.category_id = None
        
        # 기존 태그 삭제
        from app.models.post_tag import PostTag
        PostTag.query.filter_by(post_id=post.id).delete()
        
        # 태그 처리 (필요시)
        if 'tags' in data and data['tags']:
            from app.models.tag import Tag
            from app.models.post_tag import PostTag
            
            for tag_name in data['tags']:
                if not tag_name:
                    continue
                
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()  # ID 생성을 위해 플러시
                
                post_tag = PostTag(post_id=post.id, tag_id=tag.id)
                db.session.add(post_tag)
        
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        print(f"오류: {str(e)}")
        return jsonify({'success': False, 'message': f'저장 중 오류가 발생했습니다: {str(e)}'}), 500

# 포스트 삭제
@blog_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete(post_id):
    """블로그 포스트 삭제 API"""
    try:
        post = Post.query.get_or_404(post_id)
        
        if post.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        
        # 포스트 태그 관계 먼저 삭제
        from app.models.post_tag import PostTag
        PostTag.query.filter_by(post_id=post.id).delete()
        
        # 포스트 삭제
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        print(f"오류: {str(e)}")
        return jsonify({'success': False, 'message': f'삭제 중 오류가 발생했습니다: {str(e)}'}), 500

# 파일 업로드 API
@blog_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """에디터에서 이미지 업로드 API"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '선택된 파일이 없습니다.'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 중복 방지를 위해 타임스탬프 추가
        filename = f"{int(time.time())}_{filename}"
        
        # 디렉토리가 없으면 생성
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # URL 경로 반환
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({
            'success': 1,  # EditorJS 이미지 도구 규약에 맞춤
            'file': {
                'url': url
            }
        })
    
    return jsonify({'success': False, 'message': '허용되지 않는 파일 형식입니다.'}), 400