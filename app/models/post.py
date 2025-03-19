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
    # 카테고리 제거, 태그만 사용
    
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
    
    def get_formatted_content(self):
        """서식이 포함된 HTML 콘텐츠 반환"""
        try:
            content_obj = self.get_content_json()
            
            # HTML 직접 사용
            if content_obj and 'html' in content_obj:
                html_content = content_obj['html']
                
                # 문자열 처리가 필요한 경우
                if isinstance(html_content, str):
                    # 이스케이프된 문자 처리
                    html_content = html_content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                
                return html_content
                
            # 블록 포맷 처리 (기존 호환성)
            elif 'blocks' in content_obj:
                html = ''
                for block in content_obj.get('blocks', []):
                    if block.get('type') == 'paragraph':
                        html += f"<p>{block.get('content', '')}</p>"
                    elif block.get('type') == 'header':
                        level = min(max(block.get('level', 1), 1), 6)
                        html += f"<h{level}>{block.get('content', '')}</h{level}>"
                    elif block.get('type') == 'quote':
                        html += f"<blockquote>{block.get('content', '')}</blockquote>"
                    elif block.get('type') == 'code':
                        language = block.get('language', 'plaintext')
                        content = block.get('content', '')
                        html += f"<pre><code class=\"language-{language}\">{content}</code></pre>"
                    elif block.get('type') == 'list':
                        list_type = 'ol' if block.get('style') == 'ordered' else 'ul'
                        html += f"<{list_type}>"
                        for item in block.get('items', []):
                            html += f"<li>{item}</li>"
                        html += f"</{list_type}>"
                    elif block.get('type') == 'image':
                        style = ''
                        if block.get('width'): style += f"width: {block.get('width')};"
                        if block.get('height'): style += f"height: {block.get('height')};"
                        
                        html += f"<img src=\"{block.get('url', '')}\" alt=\"{block.get('alt', '')}\" style=\"{style}\" class=\"editor-image\">"
                        
                        if block.get('caption'):
                            html += f"<figcaption>{block.get('caption')}</figcaption>"
                    elif block.get('type') == 'embed':
                        html += block.get('html', '')
                    elif block.get('type') == 'table':
                        html += '<table class="editor-table"><tbody>'
                        for row in block.get('rows', []):
                            html += '<tr>'
                            for cell in row:
                                cell_tag = 'th' if cell.get('isHeader') else 'td'
                                html += f"<{cell_tag}>{cell.get('content', '')}</{cell_tag}>"
                            html += '</tr>'
                        html += '</tbody></table>'
                    elif block.get('type') == 'delimiter':
                        html += '<hr>'
                return html
                
            # 기본값 반환
            return self.content
        except Exception as e:
            print(f"콘텐츠 변환 오류: {str(e)}")
            return self.content