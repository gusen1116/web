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
    tags = db.relationship('Tag', secondary='post_tags', backref='posts')
    
    def get_content_json(self):
        return json.loads(self.content)
    
    def set_content_json(self, content_obj):
        self.content = json.dumps(content_obj)
        
    def get_preview(self, length=200):
        content_json = self.get_content_json()
        preview_text = ""
        
        # EditorJS 블록에서 텍스트 추출
        for block in content_json.get('blocks', []):
            if block.get('type') == 'paragraph':
                preview_text += block.get('data', {}).get('text', '') + " "
                
        return preview_text[:length] + "..." if len(preview_text) > length else preview_text