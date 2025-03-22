# app/services/text_service.py
import os
import re
import shutil
from datetime import datetime
import markdown
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
        self.created_at = datetime.now()  # 호환성을 위해 추가
        self.tags = []
        self.author = "관리자"
        self.description = ""
        self.slug = None  # URL 슬러그 추가
        
        # 메타데이터가 제공된 경우 업데이트
        if metadata:
            self.title = metadata.get('title', self.title)
            self.description = metadata.get('description', '')
            self.author = metadata.get('author', self.author)
            
            # 슬러그 설정
            self.slug = metadata.get('slug', self.id)
            
            # 날짜 파싱
            date_str = metadata.get('date')
            if date_str:
                try:
                    self.date = datetime.strptime(date_str, '%Y-%m-%d')
                    self.created_at = self.date
                except ValueError:
                    pass
            
            # 태그 파싱
            tags_str = metadata.get('tags')
            if tags_str:
                self.tags = [tag.strip() for tag in tags_str.split(',')]
    
    def get_url(self):
        """포스트 URL 반환"""
        if hasattr(self, 'slug') and self.slug:
            return url_for('posts.view_by_slug', slug=self.slug)
        return url_for('posts.view_by_slug', slug=self.id)


    def get_preview(self, length=200):
        """본문 미리보기 생성"""
        # 특수 태그 제거
        text = re.sub(r'\[img:[^\]]+\]', '', self.content)
        text = re.sub(r'\[file:[^\]]+\]', '', text)
        text = re.sub(r'#+ ', '', text)  # 마크다운 헤더 태그 제거
        text = re.sub(r'\*\*|\*|__', '', text)  # 강조 태그 제거
        
        # 길이 제한
        if len(text) > length:
            return text[:length] + "..."
        return text
    
    def get_word_count(self):
        """글자 수 반환"""
        # 특수 태그 제거
        text = re.sub(r'\[img:[^\]]+\]', '', self.content)
        text = re.sub(r'\[file:[^\]]+\]', '', text)
        
        # 단어 수 계산
        words = re.findall(r'\w+', text)
        return len(words)
    
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
    # 마크다운 변환을 위해 마크다운 라이브러리 사용
    md = markdown.Markdown(extensions=['extra', 'codehilite'])
    
    # 이미지 태그 변환
    content = re.sub(
        r'\[img:([^\]]+)(?:\|([^\]]+))?\]',
        lambda m: f'<figure class="post-image"><img src="{base_url_images}/{m.group(1)}" alt="{m.group(2) if m.group(2) else m.group(1)}" class="text-post-image"><figcaption>{m.group(2) if m.group(2) else ""}</figcaption></figure>',
        content
    )
    
    # 파일 태그 변환
    content = re.sub(
        r'\[file:([^|\]]+)(?:\|([^\]]+))?\]',
        lambda m: f'<a href="{base_url_files}/{m.group(1)}" class="file-download" download><i class="fas fa-download"></i> {m.group(2) if m.group(2) else m.group(1)}</a>',
        content
    )
    
    # 마크다운 변환
    html_content = md.convert(content)
    
    return html_content


def get_all_text_posts(text_dir, tag=None):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환"""
    posts = []
    
    try:
        for filename in os.listdir(text_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(text_dir, filename)
                metadata, content = parse_text_file(file_path)
                post = TextPost(filename, content, metadata)
                
                # 태그 필터링
                if tag is None or tag in post.tags:
                    posts.append(post)
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


def find_related_posts(text_dir, current_post, limit=3):
    """관련 포스트 찾기 (태그 기반)"""
    if not current_post or not current_post.tags:
        return []
    
    all_posts = get_all_text_posts(text_dir)
    related_posts = []
    
    # 현재 포스트 제외
    all_posts = [p for p in all_posts if p.filename != current_post.filename]
    
    # 태그 일치 점수 계산
    for post in all_posts:
        common_tags = set(post.tags) & set(current_post.tags)
        score = len(common_tags)
        if score > 0:
            related_posts.append((post, score))
    
    # 일치 점수 기준 정렬
    related_posts.sort(key=lambda x: x[1], reverse=True)
    
    # 상위 N개 반환
    return [post for post, _ in related_posts[:limit]]


def search_posts(text_dir, query):
    """포스트 검색"""
    if not query:
        return []
    
    query = query.lower()
    results = []
    
    all_posts = get_all_text_posts(text_dir)
    for post in all_posts:
        # 제목, 내용, 태그에서 검색
        if (query in post.title.lower() or 
            query in post.content.lower() or 
            any(query in tag.lower() for tag in post.tags)):
            results.append(post)
    
    return results
