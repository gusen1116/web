# app/models/category.py
from app import db

class Category(db.Model):
    __tablename__ = 'categories'  # 명시적 테이블 이름
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # 관계 정의
    posts = db.relationship('Post', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'