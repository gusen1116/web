# app/models/post_tag.py
from app import db
def get_preview(self, length=200):
    try:
        # 마크다운에서는 JSON이 아닌 일반 텍스트를 처리합니다
        preview_text = self.content
        
        # HTML 태그 제거
        import re
        preview_text = re.sub(r'<[^>]*>', '', preview_text)
        
        # 마크다운 특수 문자 제거
        preview_text = re.sub(r'[#*_~`\[\]\(\)\{\}\|]', '', preview_text)
        
        # 길이 제한 및 "..." 추가
        if len(preview_text) > length:
            return preview_text[:length] + "..."
        return preview_text
    except Exception:
        return ""

class PostTag(db.Model):
    __tablename__ = 'post_tags'
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    
    def __repr__(self):
        return f'<PostTag {self.post_id}:{self.tag_id}>'
    
    