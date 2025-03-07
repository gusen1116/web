# app/models/post_tag.py
from app import db

class PostTag(db.Model):
    __tablename__ = 'post_tags'  # 명시적 테이블 이름
    
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)  # 외래 키 경로 수정
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)  # 외래 키 경로 수정
    
    def __repr__(self):
        return f'<PostTag {self.post_id}:{self.tag_id}>'