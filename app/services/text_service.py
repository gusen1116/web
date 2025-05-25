# app/models/text_post.py
import os
import re
from datetime import datetime
from flask import url_for
from markupsafe import escape

class TextPost:
    """간소화된 텍스트 포스트 모델"""
    
    def __init__(self, filename, content, metadata=None):
        self.filename = self._safe_filename(filename)
        self.content = content
        self.id = os.path.splitext(self.filename)[0]
        
        # 기본값 설정
        self._set_defaults()
        
        # 메타데이터 적용
        if metadata:
            self._apply_metadata(metadata)
    
    def _safe_filename(self, filename):
        """안전한 파일명 검증"""
        if not isinstance(filename, str) or not filename:
            raise ValueError("잘못된 파일명")
        
        # 위험한 패턴 검사
        dangerous = ['..', '/', '\\', '\x00']
        if any(p in filename for p in dangerous):
            raise ValueError("잘못된 파일명")
        
        if filename.startswith('.') or len(filename) > 255:
            raise ValueError("잘못된 파일명")
        
        return filename
    
    def _set_defaults(self):
        """기본값 설정"""
        now = datetime.now()
        self.title = self.filename
        self.date = now
        self.created_at = now
        self.tags = []
        self.author = "구센"
        self.description = ""
        self.subtitle = ""
        self.slug = self.id
        self.series = None
        self.series_part = None
    
    def _apply_metadata(self, metadata):
        """메타데이터 적용"""
        safe_fields = {
            'title': str,
            'description': str,
            'subtitle': str,
            'author': str,
            'slug': str,
            'series': str
        }
        
        for field, field_type in safe_fields.items():
            if field in metadata and isinstance(metadata[field], field_type):
                setattr(self, field, escape(metadata[field]))
        
        # 날짜 파싱
        if 'date' in metadata:
            try:
                self.date = datetime.strptime(metadata['date'], '%Y-%m-%d')
                self.created_at = self.date
            except (ValueError, TypeError):
                pass
        
        # 태그 파싱
        if 'tags' in metadata and isinstance(metadata['tags'], str):
            tags = [escape(tag.strip()) for tag in metadata['tags'].split(',')]
            self.tags = [tag for tag in tags if tag and len(tag) <= 50]
        
        # 시리즈 파트
        if 'series-part' in metadata:
            try:
                part = int(metadata['series-part'])
                if 0 < part < 1000:
                    self.series_part = part
            except (ValueError, TypeError):
                pass
    
    def get_url(self):
        """포스트 URL 반환"""
        return url_for('posts.view_by_slug', slug=self.slug or self.id)
    
    def get_preview(self, length=None):
        """미리보기 텍스트 생성"""
        from flask import current_app
        length = length or current_app.config.get('MAX_PREVIEW_LENGTH', 300)
        
        # 마크다운 태그 제거
        clean_text = re.sub(r'\[.*?\]', '', self.content)
        clean_text = re.sub(r'[#*`]', '', clean_text)
        clean_text = ' '.join(clean_text.split())
        
        if len(clean_text) > length:
            return escape(clean_text[:length] + "...")
        return escape(clean_text)
    
    def get_word_count(self):
        """단어 수 반환"""
        text = re.sub(r'\[.*?\]', '', self.content)
        words = re.findall(r'\w+', text)
        return min(len(words), 100000)