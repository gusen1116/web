# app/services/text_service.py
import os
import re
import time
from datetime import datetime
from flask import url_for, current_app
from markupsafe import escape, Markup
import hashlib

# 마크다운 처리를 위한 임포트
try:
    import markdown
    import bleach
    MARKDOWN_ENABLED = True
except ImportError:
    MARKDOWN_ENABLED = False

# 상수 정의
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_POSTS = 1000
MAX_TAG_LENGTH = 50
MAX_TITLE_LENGTH = 200
MAX_PREVIEW_LENGTH = 1000
CACHE_VERSION = "v1"  # 캐시 버전 관리

class TextPost:
    """텍스트 파일 기반 포스트 클래스"""
    
    def __init__(self, filename, content, metadata=None):
        # 파일명 검증
        if not self._validate_filename(filename):
            raise ValueError("잘못된 파일명입니다")
            
        self.filename = filename
        self.content = content
        self.id = os.path.splitext(self.filename)[0]
        self._hash = None  # 파일 해시 캐싱
        
        # 메타데이터 기본값
        self.title = self.filename
        self.date = datetime.now()
        self.created_at = datetime.now()
        self.tags = []
        self.author = "구센"
        self.description = ""
        self.subtitle = ""
        self.slug = None
        self.series = None
        self.series_part = None
        self.changelog = []
        
        # 메타데이터 업데이트
        if metadata:
            self._update_metadata(metadata)
    
    @staticmethod
    def _validate_filename(filename):
        """파일명 유효성 검사"""
        if not isinstance(filename, str) or not filename:
            return False
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        if filename.startswith('.'):
            return False
        if len(filename) > 255:
            return False
        if not filename.endswith('.txt'):
            return False
        # 안전한 문자만 허용
        if not re.match(r'^[a-zA-Z0-9_\-가-힣\s]+\.txt$', filename):
            return False
        return True
    
    def _update_metadata(self, metadata):
        """메타데이터 안전하게 업데이트"""
        # 제목
        if 'title' in metadata:
            title = str(metadata['title'])[:MAX_TITLE_LENGTH]
            self.title = escape(title)
            
        # 설명
        if 'description' in metadata:
            desc = str(metadata['description'])[:500]
            self.description = escape(desc)
            
        # 부제목
        if 'subtitle' in metadata:
            subtitle = str(metadata['subtitle'])[:200]
            self.subtitle = escape(subtitle)
            
        # 작성자
        if 'author' in metadata:
            author = str(metadata['author'])[:50]
            self.author = escape(author)
            
        # 슬러그 설정
        if 'slug' in metadata:
            slug = str(metadata['slug'])[:100]
            # 슬러그는 URL에 사용되므로 엄격한 검증
            if re.match(r'^[a-zA-Z0-9_\-]+$', slug):
                self.slug = slug
            else:
                self.slug = self.id
        else:
            self.slug = self.id
        
        # 날짜 파싱
        if 'date' in metadata:
            try:
                date_str = str(metadata['date'])
                self.date = datetime.strptime(date_str, '%Y-%m-%d')
                self.created_at = self.date
            except ValueError:
                current_app.logger.warning(f"잘못된 날짜 형식: {date_str}")
        
        # 태그 파싱
        if 'tags' in metadata:
            tags_str = str(metadata['tags'])
            self.tags = []
            for tag in tags_str.split(','):
                tag = tag.strip()
                if tag and len(tag) <= MAX_TAG_LENGTH:
                    # 태그 검증: 한글, 영문, 숫자, 공백만 허용
                    if re.match(r'^[가-힣a-zA-Z0-9\s]+$', tag):
                        self.tags.append(escape(tag))
        
        # 시리즈 정보
        if 'series' in metadata:
            series = str(metadata['series'])[:100]
            if re.match(r'^[가-힣a-zA-Z0-9\s\-]+$', series):
                self.series = escape(series)
        
        if 'series-part' in metadata:
            try:
                part = int(metadata['series-part'])
                if 0 < part < 1000:
                    self.series_part = part
            except ValueError:
                pass
        
        # 수정 이력
        if 'changelog' in metadata:
            changelog_str = str(metadata['changelog'])
            self.changelog = []
            for item in changelog_str.split(','):
                item = item.strip()[:200]
                if item:
                    self.changelog.append(escape(item))
    
    def get_url(self):
        """포스트 URL 반환"""
        if self.slug:
            return url_for('posts.view_by_slug', slug=self.slug)
        return url_for('posts.view_by_slug', slug=self.id)

    def get_preview(self, length=200):
        """본문 미리보기 생성"""
        length = min(max(50, int(length)), MAX_PREVIEW_LENGTH)
        
        # 특수 태그 제거를 위한 패턴
        patterns = [
            r'\[img:[^\]]+\]',
            r'\[video:[^\]]+\]',
            r'\[audio:[^\]]+\]',
            r'\[youtube:[^\]]+\]',
            r'\[twitch:[^\]]+\]',
            r'\[twitter:[^\]]+\]',
            r'\[instagram:[^\]]+\]',
            r'\[facebook:[^\]]+\]',
            r'\[highlight\].*?\[/highlight\]',
            r'\[quote.*?\].*?\[/quote\]',
            r'\[.*?\]',  # 기타 태그
            r'#+\s+',    # 마크다운 헤더
            r'\*\*|\*|__|_',  # 마크다운 강조
            r'!\[.*?\]\(.*?\)',  # 마크다운 이미지
            r'\[.*?\]\(.*?\)',   # 마크다운 링크
        ]
        
        text = self.content
        for pattern in patterns:
            text = re.sub(pattern, ' ', text, flags=re.DOTALL | re.MULTILINE)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 길이 제한
        if len(text) > length:
            # 단어 경계에서 자르기
            preview = text[:length]
            last_space = preview.rfind(' ')
            if last_space > length * 0.8:  # 80% 이상 위치에 공백이 있으면
                preview = preview[:last_space]
            preview += "..."
        else:
            preview = text
            
        return escape(preview)
    
    def get_word_count(self):
        """글자 수 반환"""
        # 특수 태그 제거
        text = re.sub(r'\[.*?\]', '', self.content, flags=re.DOTALL)
        text = re.sub(r'[#*_`~]', '', text)
        
        # 단어 카운트
        words = re.findall(r'\w+', text)
        return len(words)
    
    def get_file_hash(self):
        """파일 해시 반환 (캐싱)"""
        if not self._hash:
            content = f"{self.filename}:{self.content}:{CACHE_VERSION}"
            self._hash = hashlib.md5(content.encode()).hexdigest()
        return self._hash


def parse_text_file(file_path):
    """텍스트 파일 파싱하여 메타데이터와 본문 분리"""
    if not isinstance(file_path, str) or not file_path.endswith('.txt'):
        return {}, ""
    
    # 경로 검증
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        return {}, ""
    
    try:
        # 파일 크기 검사
        if os.path.getsize(abs_path) > MAX_FILE_SIZE:
            current_app.logger.warning(f"파일 크기 초과: {file_path}")
            return {}, "파일 크기가 너무 큽니다"
        
        # 파일 읽기
        with open(abs_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 메타데이터 추출
        metadata = {}
        content_lines = content.split('\n')
        content_start = 0
        
        # 메타데이터 패턴: [key: value]
        meta_pattern = re.compile(r'^\[([a-zA-Z\-]+):\s*(.+?)\]$')
        
        for i, line in enumerate(content_lines):
            match = meta_pattern.match(line)
            if match:
                key, value = match.groups()
                # 키 검증 (알파벳과 하이픈만)
                if re.match(r'^[a-zA-Z\-]+$', key) and len(key) <= 50:
                    metadata[key.lower()] = value
                content_start = i + 1
            else:
                # 메타데이터가 아닌 줄을 만나면 중단
                break
        
        # 본문 추출
        body_content = '\n'.join(content_lines[content_start:]).strip()
        
        return metadata, body_content
        
    except Exception as e:
        current_app.logger.error(f"파일 파싱 오류 {file_path}: {str(e)}")
        return {}, ""


def get_all_text_posts(posts_dir=None, tag=None):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환"""
    if posts_dir is None:
        posts_dir = current_app.config.get('POSTS_DIR')
    
    posts = []
    
    try:
        # 디렉토리 존재 확인
        if not os.path.exists(posts_dir) or not os.path.isdir(posts_dir):
            current_app.logger.warning(f"포스트 디렉토리 없음: {posts_dir}")
            return posts
        
        # 파일 목록 가져오기 (제한)
        filenames = sorted(os.listdir(posts_dir))[:MAX_POSTS]
        
        for filename in filenames:
            if filename.endswith('.txt') and not filename.startswith('.'):
                post = get_text_post(posts_dir, filename)
                if post:
                    posts.append(post)
        
        # 날짜순 정렬 (최신순)
        posts.sort(key=lambda x: x.date, reverse=True)
        
        # 태그 필터링
        if tag:
            posts = [p for p in posts if tag in p.tags]
            
    except Exception as e:
        current_app.logger.error(f"포스트 로드 오류: {str(e)}")
    
    return posts


def get_text_post(posts_dir, filename):
    """특정 텍스트 파일 로드하여 TextPost 객체 반환"""
    try:
        # 파일명 검증
        if not TextPost._validate_filename(filename):
            return None
        
        file_path = os.path.join(posts_dir, filename)
        abs_path = os.path.abspath(file_path)
        
        # 경로 검증
        if not abs_path.startswith(os.path.abspath(posts_dir)):
            current_app.logger.warning(f"경로 위반 시도: {filename}")
            return None
        
        # 파일 존재 및 크기 확인
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return None
            
        if os.path.getsize(abs_path) > MAX_FILE_SIZE:
            current_app.logger.warning(f"파일 크기 초과: {filename}")
            return None
        
        # 파일 파싱
        metadata, content = parse_text_file(abs_path)
        
        return TextPost(filename, content, metadata)
        
    except Exception as e:
        current_app.logger.error(f"포스트 로드 오류 {filename}: {str(e)}")
        return None


def get_tags_count(posts_dir=None):
    """모든 텍스트 파일의 태그 카운트 반환"""
    tags_count = {}
    
    try:
        posts = get_all_text_posts(posts_dir)
        for post in posts:
            for tag in post.tags:
                if tag in tags_count:
                    tags_count[tag] += 1
                else:
                    tags_count[tag] = 1
    except Exception as e:
        current_app.logger.error(f"태그 카운트 오류: {str(e)}")
    
    return tags_count


def get_series_posts(posts_dir, series_name):
    """시리즈에 속한 모든 포스트 검색"""
    if not series_name or not isinstance(series_name, str):
        return []
    
    series_posts = []
    
    try:
        all_posts = get_all_text_posts(posts_dir)
        
        for post in all_posts:
            if hasattr(post, 'series') and post.series == series_name:
                series_posts.append(post)
        
        # 시리즈 파트 순서대로 정렬
        series_posts.sort(key=lambda x: (x.series_part or 9999, x.date))
        
    except Exception as e:
        current_app.logger.error(f"시리즈 포스트 로드 오류: {str(e)}")
    
    return series_posts


def get_adjacent_posts(posts_dir, current_post):
    """현재 포스트의 이전 및 다음 포스트 반환"""
    if not current_post or not isinstance(current_post, TextPost):
        return None, None
    
    try:
        all_posts = get_all_text_posts(posts_dir)
        
        # 날짜순으로 정렬 (최신순)
        all_posts.sort(key=lambda x: x.date, reverse=True)
        
        # 현재 포스트 찾기
        current_index = None
        for i, post in enumerate(all_posts):
            if post.id == current_post.id:
                current_index = i
                break
        
        if current_index is None:
            return None, None
        
        # 이전 포스트 (더 최신)
        prev_post = all_posts[current_index - 1] if current_index > 0 else None
        
        # 다음 포스트 (더 오래된)
        next_post = all_posts[current_index + 1] if current_index < len(all_posts) - 1 else None
        
        return prev_post, next_post
        
    except Exception as e:
        current_app.logger.error(f"인접 포스트 조회 오류: {str(e)}")
        return None, None


# 안전한 HTML 렌더링을 위한 헬퍼 함수들
def _safe_url(url, allowed_domains=None):
    """URL 안전성 검증"""
    if not url or not isinstance(url, str):
        return False
    
    # 기본 검증
    url_lower = url.lower()
    if url_lower.startswith(('javascript:', 'data:', 'vbscript:')):
        return False
    
    # 도메인 검증 (필요한 경우)
    if allowed_domains:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc and parsed.netloc not in allowed_domains:
            return False
    
    return True


def _create_youtube_embed(youtube_id_or_url):
    """유튜브 임베드 HTML 생성 (보안 강화)"""
    youtube_id = ""
    
    if not isinstance(youtube_id_or_url, str):
        return '<div class="error-embed">잘못된 YouTube URL</div>'
    
    # YouTube ID 추출
    if 'youtube.com' in youtube_id_or_url or 'youtu.be' in youtube_id_or_url:
        # URL에서 ID 추출
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_\-]{11})',
            r'youtu\.be/([a-zA-Z0-9_\-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_\-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_id_or_url)
            if match:
                youtube_id = match.group(1)
                break
    else:
        # 직접 ID인 경우
        if re.match(r'^[a-zA-Z0-9_\-]{11}$', youtube_id_or_url):
            youtube_id = youtube_id_or_url
    
    if not youtube_id:
        return '<div class="error-embed">잘못된 YouTube ID</div>'
    
    # 안전한 ID만 사용
    safe_id = escape(youtube_id)
    
    return f'''
<div class="social-embed youtube-embed">
    <iframe src="https://www.youtube.com/embed/{safe_id}" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen
            sandbox="allow-scripts allow-same-origin allow-presentation"
            loading="lazy"></iframe>
</div>
'''


def _create_image_tag(src, alt=None, base_url='/'):
    """안전한 이미지 태그 생성"""
    if not isinstance(src, str) or not src:
        return '<div class="error-embed">잘못된 이미지 경로</div>'
    
    # 파일명 검증
    if not re.match(r'^[a-zA-Z0-9_\-가-힣\s]+\.(jpg|jpeg|png|gif|webp|svg)$', src, re.IGNORECASE):
        return '<div class="error-embed">잘못된 이미지 파일명</div>'
    
    safe_src = escape(src)
    safe_alt = escape(alt) if alt else escape(src)
    
    return f'''
<figure class="post-image">
    <img src="{base_url}/{safe_src}" 
         alt="{safe_alt}" 
         class="text-post-image"
         loading="lazy">
    {f'<figcaption>{safe_alt}</figcaption>' if alt else ''}
</figure>
'''


def render_content(content, base_url_images='/posts/images', 
                   base_url_videos='/posts/videos', 
                   base_url_audios='/posts/audios'):
    """특수 태그를 HTML로 변환 후 마크다운 처리"""
    if not isinstance(content, str):
        return ""
    
    # URL 검증
    for url in [base_url_images, base_url_videos, base_url_audios]:
        if not isinstance(url, str) or not url.startswith('/'):
            return "잘못된 URL 설정"
    
    # 특수 태그 처리
    replacements = [
        # YouTube
        (r'\[youtube:([^\]]+)\]', 
         lambda m: _create_youtube_embed(m.group(1))),
        
        # 이미지
        (r'\[img:([^\]|]+)(?:\|([^\]]+))?\]', 
         lambda m: _create_image_tag(m.group(1), m.group(2), base_url_images)),
        
        # 하이라이트
        (r'\[highlight\](.*?)\[/highlight\]', 
         lambda m: f'<div class="highlight-box">{escape(m.group(1))}</div>'),
        
        # 인용구
        (r'\[quote(?:\s+author="([^"]*)")?\](.*?)\[/quote\]', 
         lambda m: f'''<blockquote class="styled-quote">
            {escape(m.group(2))}
            {f'<span class="quote-author">{escape(m.group(1))}</span>' if m.group(1) else ''}
         </blockquote>'''),
    ]
    
    # 특수 태그 변환
    for pattern, handler in replacements:
        content = re.sub(pattern, handler, content, flags=re.DOTALL | re.MULTILINE)
    
    # 마크다운 처리
    if MARKDOWN_ENABLED:
        try:
            # 마크다운 변환
            md = markdown.Markdown(
                extensions=['extra', 'nl2br', 'sane_lists', 'codehilite'],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight',
                        'linenums': False,
                        'guess_lang': True
                    }
                }
            )
            
            html_content = md.convert(content)
            
            # HTML 정제 (XSS 방지)
            allowed_tags = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                'p', 'br', 'hr', 'a', 'strong', 'em', 
                'code', 'pre', 'blockquote', 'img',
                'ul', 'ol', 'li', 'span', 'div', 
                'figure', 'figcaption', 'table', 'thead',
                'tbody', 'tr', 'th', 'td', 'iframe'
            ]
            
            allowed_attrs = {
                'a': ['href', 'title', 'target', 'rel', 'class'],
                'img': ['src', 'alt', 'title', 'width', 'height', 'class', 'loading'],
                'div': ['class'],
                'span': ['class'],
                'code': ['class'],
                'pre': ['class'],
                'iframe': ['src', 'width', 'height', 'frameborder', 
                          'allowfullscreen', 'allow', 'sandbox', 'loading'],
                'blockquote': ['class'],
                'figure': ['class'],
                'figcaption': ['class']
            }
            
            cleaned_content = bleach.clean(
                html_content, 
                tags=allowed_tags, 
                attributes=allowed_attrs,
                strip=True
            )
            
            # 자동 링크 변환
            cleaned_content = _auto_linkify_urls(cleaned_content)
            
        except Exception as e:
            current_app.logger.error(f"마크다운 처리 오류: {str(e)}")
            # 폴백: 기본 처리
            cleaned_content = _process_content_fallback(content)
    else:
        # 마크다운 라이브러리 없을 때
        cleaned_content = _process_content_fallback(content)
    
    return Markup(cleaned_content)


def _auto_linkify_urls(text):
    """URL 자동 링크 변환 (보안 강화)"""
    if not isinstance(text, str):
        return text
    
    # 이미 링크인 부분은 제외하고 URL 찾기
    url_pattern = re.compile(
        r'(?<!href=")(?<!src=")'
        r'(https?://[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+)',
        re.IGNORECASE
    )
    
    def url_replacer(match):
        url = match.group(1)
        
        # URL 끝의 문장부호 제거
        url = url.rstrip('.,;:!?')
        
        # URL 안전성 검증
        if not _safe_url(url):
            return url
        
        # 보안을 위한 URL 이스케이핑
        safe_url = escape(url)
        
        # 표시 텍스트 생성
        display_text = url
        if len(url) > 60:
            display_text = url[:57] + "..."
        
        return (f'<a href="{safe_url}" '
                f'target="_blank" '
                f'rel="noopener noreferrer nofollow" '
                f'class="auto-link">{escape(display_text)}</a>')
    
    return url_pattern.sub(url_replacer, text)


def _process_content_fallback(content):
    """마크다운 라이브러리 없을 때 기본 처리"""
    lines = content.split('\n')
    processed_lines = []
    in_code_block = False
    current_paragraph = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 빈 줄
        if not line_stripped:
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            processed_lines.append('<br>')
            continue
        
        # 코드 블록
        if line_stripped.startswith('```'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            
            if not in_code_block:
                language = line_stripped[3:].strip()
                safe_lang = escape(language) if language else 'plaintext'
                in_code_block = True
                processed_lines.append(f'<pre><code class="language-{safe_lang}">')
            else:
                in_code_block = False
                processed_lines.append('</code></pre>')
            continue
        
        # 코드 블록 내부
        if in_code_block:
            processed_lines.append(escape(line))
            continue
        
        # 헤더
        if line_stripped.startswith('#'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            
            header_match = re.match(r'^(#+)\s+(.+)$', line_stripped)
            if header_match:
                level = len(header_match.group(1))
                level = min(max(level, 1), 6)  # 1-6 범위로 제한
                header_text = escape(header_match.group(2))
                processed_lines.append(f'<h{level}>{header_text}</h{level}>')
                continue
        
        # 일반 텍스트
        current_paragraph.append(escape(line_stripped))
    
    # 마지막 단락 처리
    if current_paragraph:
        paragraph_text = " ".join(current_paragraph)
        paragraph_text = _auto_linkify_urls(paragraph_text)
        processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
    
    return '\n'.join(processed_lines)