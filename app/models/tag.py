# app/models/tag.py
from app import db

class Tag(db.Model):
    __tablename__ = 'tags'  # 명시적 테이블 이름
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Tag {self.name}>'