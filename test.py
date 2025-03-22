# 임시 스크립트: /Users/jinhyundoo/web/clear_db.py
from app import create_app, db
from app.models import Post, Category, Tag, PostTag

app = create_app()

with app.app_context():
    # 모든 관계 데이터 제거
    PostTag.query.delete()
    
    # 모든 포스트 제거
    Post.query.delete()
    
    # 모든 태그 제거
    Tag.query.delete()
    
    # 모든 카테고리 제거
    Category.query.delete()
    
    # 변경사항 저장
    db.session.commit()
    
    print("모든 블로그 데이터가 성공적으로 제거되었습니다.")