# app/models/file.py
from app import db
from datetime import datetime

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # 원본 파일명
    stored_filename = db.Column(db.String(255), nullable=False)  # 저장된 파일명
    file_path = db.Column(db.String(512), nullable=False)  # 파일 시스템 경로
    file_url = db.Column(db.String(512), nullable=False)  # 접근 URL
    file_type = db.Column(db.String(50), nullable=False)  # 파일 타입 (image, document, archive 등)
    file_size = db.Column(db.Integer, nullable=False)  # 파일 크기 (바이트)
    file_hash = db.Column(db.String(32), unique=True, nullable=False)  # MD5 해시 (중복 확인용)
    is_image = db.Column(db.Boolean, default=False)  # 이미지 여부
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)  # 업로드 날짜
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 업로더 ID (없을 수 있음)
    
    def __repr__(self):
        return f'<File {self.filename}>'