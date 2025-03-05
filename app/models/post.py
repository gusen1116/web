# app/models/post.py
from app import db
from datetime import datetime
import json

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
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
            
            # EditorJS 블록에서 텍스트 추출
            for block in content_json.get('blocks', []):
                if block.get('type') == 'paragraph':
                    preview_text += block.get('data', {}).get('text', '') + " "
            
            # 길이 제한 및 "..." 추가
            if len(preview_text) > length:
                return preview_text[:length] + "..."
            return preview_text
        except Exception:
            return ""