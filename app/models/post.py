# app/models/post.py
from app import db
from datetime import datetime
import json

class Post(db.Model):
    __tablename__ = 'posts'  # 명시적 테이블 이름
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 외래 키 경로 수정
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # 외래 키 경로 수정
    
    # tags 관계는 PostTag 모델을 통해 간접적으로 정의
    tags = db.relationship('Tag', secondary='post_tags', backref=db.backref('posts', lazy='dynamic'))
    
    def get_content_json(self):
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:
            return {"blocks": []}
    
    def set_content_json(self, content_obj):
        self.content = json.dumps(content_obj)
        
    def get_preview(self, length=200):
        try:
            content_json = self.get_content_json()
            preview_text = ""
            
            # 블록에서 텍스트 추출
            for block in content_json.get('blocks', []):
                if block.get('type') in ['paragraph', 'header', 'quote']:
                    # HTML 태그 제거
                    import re
                    content = re.sub(r'<[^>]*>', '', block.get('content', ''))
                    preview_text += content + " "
                elif block.get('type') == 'list':
                    for item in block.get('items', []):
                        item_text = re.sub(r'<[^>]*>', '', item)
                        preview_text += "• " + item_text + " "
            
            # 길이 제한 및 "..." 추가
            if len(preview_text) > length:
                return preview_text[:length] + "..."
            return preview_text
        except Exception as e:
            print(f"미리보기 생성 오류: {str(e)}")
            return ""