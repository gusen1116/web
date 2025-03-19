# app/services/text_service.py
import os
import re
from datetime import datetime
from flask import url_for

class TextPost:
    """텍스트 파일 기반 포스트 클래스"""
    
    def __init__(self, filename, content, metadata=None):
        self.filename = filename
        self.content = content
        self.id = os.path.splitext(filename)[0]
        
        # 메타데이터 기본값
        self.title = filename
        self.date = datetime.now()
        self.tags = []
        
        # 메타데이터가 제공된 경우 업데이트
        if metadata:
            self.title = metadata.get('title', self.title)
            
            # 날짜 파싱
            date_str = metadata.get('date')
            if date_str:
                try:
                    self.date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    pass
            
            # 태그 파싱
            tags_str = metadata.get('tags')
            if tags_str:
                self.tags = [tag.strip() for tag in tags_str.split(',')]
    
    def get_url(self):
        """포스트 URL 반환"""
        return url_for('texts.view_text', filename=self.filename)
    
    def get_preview(self, length=200):
        """본문 미리보기 생성"""
        # 이미지 태그 제거
        text = re.sub(r'\[img:[^\]]+\]', '', self.content)
        # 파일 태그 제거
        text = re.sub(r'\[file:[^\]]+\]', '', text)
        
        # 길이 제한
        if len(text) > length:
            return text[:length] + "..."
        return text


def parse_text_file(file_path):
    """텍스트 파일 파싱하여 메타데이터와 본문 분리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 메타데이터 추출
        metadata = {}
        content_lines = content.split('\n')
        content_start = 0
        
        for i, line in enumerate(content_lines):
            meta_match = re.match(r'\[(\w+):\s*(.*?)\]', line)
            if meta_match:
                key, value = meta_match.groups()
                metadata[key.lower()] = value
                content_start = i + 1
            else:
                break
        
        # 본문 추출
        body_content = '\n'.join(content_lines[content_start:])
        
        return metadata, body_content
    
    except Exception as e:
        print(f"파일 파싱 오류: {str(e)}")
        return {}, ""


def render_content(content, base_url_images, base_url_files):
    """특수 태그를 HTML로 변환"""
    # 이미지 태그 변환
    content = re.sub(
        r'\[img:([^\]]+)\]',
        lambda m: f'<img src="{base_url_images}/{m.group(1)}" alt="{m.group(1)}" class="text-post-image">',
        content
    )
    
    # 파일 태그 변환
    content = re.sub(
        r'\[file:([^|\]]+)(?:\|([^\]]+))?\]',
        lambda m: f'<a href="{base_url_files}/{m.group(1)}" class="file-download" download><i class="fas fa-download"></i> {m.group(2) if m.group(2) else m.group(1)}</a>',
        content
    )
    
    # 줄바꿈 처리
    content = content.replace('\n\n', '</p><p>')
    content = content.replace('\n', '<br>')
    
    # 최종 HTML로 래핑
    return f'<p>{content}</p>'


def get_all_text_posts(text_dir):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환"""
    posts = []
    
    try:
        for filename in os.listdir(text_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(text_dir, filename)
                metadata, content = parse_text_file(file_path)
                posts.append(TextPost(filename, content, metadata))
    except Exception as e:
        print(f"텍스트 포스트 로드 오류: {str(e)}")
    
    # 날짜순 정렬 (최신순)
    posts.sort(key=lambda x: x.date, reverse=True)
    return posts


def get_text_post(text_dir, filename):
    """특정 텍스트 파일 로드하여 TextPost 객체 반환"""
    try:
        file_path = os.path.join(text_dir, filename)
        if os.path.exists(file_path):
            metadata, content = parse_text_file(file_path)
            return TextPost(filename, content, metadata)
    except Exception as e:
        print(f"텍스트 포스트 로드 오류: {str(e)}")
    
    return None


def get_tags_count(text_dir):
    """모든 텍스트 파일의 태그 카운트 반환"""
    tags_count = {}
    
    try:
        posts = get_all_text_posts(text_dir)
        for post in posts:
            for tag in post.tags:
                if tag in tags_count:
                    tags_count[tag] += 1
                else:
                    tags_count[tag] = 1
    except Exception as e:
        print(f"태그 카운트 오류: {str(e)}")
    
    return tags_count