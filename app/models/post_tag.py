# app/models/post_tag.py
from app import db

class PostTag(db.Model):
    __tablename__ = 'post_tags'
    
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    
    def __repr__(self):
        return f'<PostTag {self.post_id}:{self.tag_id}>'