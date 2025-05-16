# app/services/text_service.py - 보안 강화 및 임베드 문제 해결
import os
import re
from datetime import datetime
import markdown
from flask import url_for
from markupsafe import escape, Markup
from werkzeug.utils import secure_filename

class TextPost:
    """텍스트 파일 기반 포스트 클래스"""
    
    def __init__(self, filename, content, metadata=None):
        # 파일명 검증
        if not isinstance(filename, str) or '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("잘못된 파일명입니다")
            
        self.filename = secure_filename(filename)
        self.content = content
        self.id = os.path.splitext(self.filename)[0]
        
        # 메타데이터 기본값
        self.title = self.filename
        self.date = datetime.now()
        self.created_at = datetime.now()  # 호환성을 위해 추가
        self.tags = []
        self.author = "관리자"
        self.description = ""
        self.slug = None  # URL 슬러그 추가
        self.series = None  # 시리즈 정보 추가
        self.series_part = None  # 시리즈 순서 추가
        self.changelog = []  # 수정 이력 추가
        
        # 메타데이터가 제공된 경우 안전하게 업데이트
        if metadata:
            # 문자열 타입 필드 검증 및 이스케이핑
            if 'title' in metadata and isinstance(metadata['title'], str):
                self.title = escape(metadata['title'])
                
            if 'description' in metadata and isinstance(metadata['description'], str):
                self.description = escape(metadata['description'])
                
            if 'author' in metadata and isinstance(metadata['author'], str):
                self.author = escape(metadata['author'])
                
            # 슬러그 설정 및 검증
            if 'slug' in metadata and isinstance(metadata['slug'], str):
                clean_slug = secure_filename(metadata['slug'])
                self.slug = clean_slug if clean_slug else self.id
            else:
                self.slug = self.id
            
            # 날짜 파싱 - 안전하게
            date_str = metadata.get('date')
            if date_str and isinstance(date_str, str):
                try:
                    self.date = datetime.strptime(date_str, '%Y-%m-%d')
                    self.created_at = self.date
                except ValueError:
                    # 날짜 형식이 잘못된 경우 기본값 유지
                    pass
            
            # 태그 파싱 - 안전하게
            tags_str = metadata.get('tags')
            if tags_str and isinstance(tags_str, str):
                clean_tags = []
                for tag in tags_str.split(','):
                    clean_tag = tag.strip()
                    if clean_tag and len(clean_tag) <= 50:  # 태그 길이 제한
                        clean_tags.append(escape(clean_tag))
                self.tags = clean_tags
            
            # 시리즈 정보 파싱 - 안전하게
            series_str = metadata.get('series')
            if series_str and isinstance(series_str, str):
                self.series = escape(series_str)
            
            series_part_str = metadata.get('series-part')
            if series_part_str and isinstance(series_part_str, str):
                try:
                    part = int(series_part_str)
                    if 0 < part < 1000:  # 합리적인 범위로 제한
                        self.series_part = part
                    else:
                        self.series_part = 1
                except ValueError:
                    self.series_part = 1
            
            # 수정 이력 파싱 - 안전하게
            changelog_str = metadata.get('changelog')
            if changelog_str and isinstance(changelog_str, str):
                clean_logs = []
                for item in changelog_str.split(','):
                    clean_item = item.strip()
                    if clean_item and len(clean_item) <= 200:  # 항목 길이 제한
                        clean_logs.append(escape(clean_item))
                self.changelog = clean_logs
    
    def get_url(self):
        """포스트 URL 반환"""
        if hasattr(self, 'slug') and self.slug:
            return url_for('posts.view_by_slug', slug=self.slug)
        return url_for('posts.view_by_slug', slug=self.id)

    def get_preview(self, length=200):
        """본문 미리보기 생성 - 안전하게"""
        if not isinstance(length, int) or length <= 0 or length > 1000:
            length = 200  # 기본값으로 안전하게 제한
            
        # 특수 태그 제거
        text = self.content
        patterns = [
            r'\[img:[^\]]+\]',
            r'\[file:[^\]]+\]',
            r'\[youtube:[^\]]+\]',
            r'\[twitch:[^\]]+\]',
            r'\[twitter:[^\]]+\]',
            r'\[instagram:[^\]]+\]',
            r'\[facebook:[^\]]+\]',
            r'\[highlight\].*?\[/highlight\]',
            r'\[quote.*?\].*?\[/quote\]',
            r'\[pullquote.*?\].*?\[/pullquote\]',
            r'\[gallery\].*?\[/gallery\]',
            r'\[related\].*?\[/related\]',
            r'\[changelog\].*?\[/changelog\]',
            r'#+ ',
            r'\*\*|\*|__'
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        # 길이 제한 및 이스케이핑
        if len(text) > length:
            preview = text[:length] + "..."
        else:
            preview = text
            
        return escape(preview)
    
    def get_word_count(self):
        """글자 수 반환 - 안전하게"""
        # 특수 태그 제거 (위와 동일한 패턴)
        text = self.content
        patterns = [
            r'\[img:[^\]]+\]',
            r'\[file:[^\]]+\]',
            r'\[youtube:[^\]]+\]',
            r'\[twitch:[^\]]+\]',
            r'\[twitter:[^\]]+\]',
            r'\[instagram:[^\]]+\]',
            r'\[facebook:[^\]]+\]',
            r'\[highlight\].*?\[/highlight\]',
            r'\[quote.*?\].*?\[/quote\]',
            r'\[pullquote.*?\].*?\[/pullquote\]',
            r'\[gallery\].*?\[/gallery\]',
            r'\[related\].*?\[/related\]',
            r'\[changelog\].*?\[/changelog\]',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        # 단어 수 계산 - 안전하게
        try:
            words = re.findall(r'\w+', text)
            return min(len(words), 100000)  # 비정상적으로 큰 값 방지
        except Exception:
            return 0  # 오류 시 기본값
    
def parse_text_file(file_path):
    """텍스트 파일 파싱하여 메타데이터와 본문 분리 - 보안 강화"""
    # 경로 검증
    if not isinstance(file_path, str):
        return {}, ""
        
    # 경로 정규화 및 검증
    abs_path = os.path.abspath(file_path)
    if '..' in file_path or not abs_path.endswith('.txt'):
        return {}, ""
    
    try:
        # 파일 크기 검증 (5MB 이하로 제한)
        if os.path.getsize(file_path) > 5 * 1024 * 1024:
            return {}, "파일 크기가 너무 큽니다"
            
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 메타데이터 추출
        metadata = {}
        content_lines = content.split('\n')
        content_start = 0
        
        for i, line in enumerate(content_lines):
            meta_match = re.match(r'\[(\w+[\-\w]*?):\s*(.*?)\]', line)
            if meta_match:
                key, value = meta_match.groups()
                # 메타데이터 키/값 검증
                if isinstance(key, str) and isinstance(value, str) and len(key) <= 50 and len(value) <= 500:
                    metadata[key.lower()] = value
                content_start = i + 1
            else:
                break
        
        # 본문 추출
        body_content = '\n'.join(content_lines[content_start:])
        
        # 텍스트 구조 확인
        lines = body_content.split('\n')
        has_markdown_header = False
        
        # 첫 번째 비어있지 않은 라인이 # 또는 ## 등으로 시작하는지 확인
        for line in lines:
            if line.strip():
                if line.strip().startswith('#'):
                    has_markdown_header = True
                break
        
        # 마크다운 헤더가 없는 경우 첫 번째 비어있지 않은 라인을 제목으로 처리
        if not has_markdown_header and 'title' in metadata:
            # 메타데이터의 title을 이미 가지고 있으므로 본문의 첫 라인이 제목인지 확인
            first_non_empty = None
            for i, line in enumerate(lines):
                if line.strip():
                    first_non_empty = i
                    break
            
            # 첫 번째 비어있지 않은 라인이 있고, 이것이 제목과 유사하다면 이를 제목으로 간주하지 않고 제거
            if first_non_empty is not None:
                title = metadata['title']
                if lines[first_non_empty].strip() == title or lines[first_non_empty].strip() in title:
                    # 유사한 제목 라인 제거
                    lines.pop(first_non_empty)
        
        # 명시적인 마크다운 헤더가 없는 경우, 첫 번째 비어있지 않은 텍스트를 h2로 만듦
        if not has_markdown_header:
            first_non_empty = None
            for i, line in enumerate(lines):
                if line.strip():
                    first_non_empty = i
                    break
            
            if first_non_empty is not None:
                lines[first_non_empty] = "## " + lines[first_non_empty]
        
        # 수정된 본문 내용
        body_content = '\n'.join(lines)
        
        return metadata, body_content
    
    except Exception as e:
        return {}, ""


def render_content(content, base_url_images, base_url_files):
    """특수 태그를 HTML로 변환 - 임베드 문제 해결"""
    if not isinstance(content, str):
        return ""
    
    # URL 검증
    if not isinstance(base_url_images, str) or not base_url_images.startswith('/'):
        base_url_images = '/posts/images'
    if not isinstance(base_url_files, str) or not base_url_files.startswith('/'):
        base_url_files = '/posts/files'
    
    # 임베드 플레이스홀더 맵 및 카운터 초기화
    placeholders = {}
    counter = 0
    
    # 1. 특수 임베드 태그 처리 및 안전한 플레이스홀더로 대체
    
    # YouTube 임베드 처리
    def youtube_handler(match):
        nonlocal counter
        youtube_id_or_url = match.group(1)
        embed_html = _create_youtube_embed(youtube_id_or_url)
        placeholder = f"__YOUTUBE_EMBED_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # Twitch 임베드 처리
    def twitch_handler(match):
        nonlocal counter
        twitch_id_or_url = match.group(1)
        embed_html = _create_twitch_embed(twitch_id_or_url)
        placeholder = f"__TWITCH_EMBED_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # Twitter 임베드 처리
    def twitter_handler(match):
        nonlocal counter
        tweet_id_or_url = match.group(1)
        embed_html = _create_twitter_embed(tweet_id_or_url)
        placeholder = f"__TWITTER_EMBED_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # Instagram 임베드 처리
    def instagram_handler(match):
        nonlocal counter
        post_id_or_url = match.group(1)
        embed_html = _create_instagram_embed(post_id_or_url)
        placeholder = f"__INSTAGRAM_EMBED_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # Facebook 임베드 처리
    def facebook_handler(match):
        nonlocal counter
        post_url = match.group(1)
        embed_html = _create_facebook_embed(post_url)
        placeholder = f"__FACEBOOK_EMBED_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # 강조 박스 처리
    def highlight_handler(match):
        nonlocal counter
        highlight_content = match.group(1)
        # 내용만 이스케이핑하고 HTML 구조는 유지
        safe_content = escape(highlight_content)
        embed_html = _create_highlight_box(safe_content)
        placeholder = f"__HIGHLIGHT_BOX_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # 인용문 처리
    def quote_handler(match):
        nonlocal counter
        author = match.group(1)
        quote_content = match.group(2)
        # 내용만 이스케이핑하고 HTML 구조는 유지
        safe_content = escape(quote_content)
        safe_author = escape(author) if author else None
        embed_html = _create_quote_box(safe_content, safe_author)
        placeholder = f"__QUOTE_BOX_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # 이미지 태그 처리
    def image_handler(match):
        nonlocal counter
        src = match.group(1)
        alt = match.group(2) if match.group(2) else None
        embed_html = _safe_image_tag(src, alt, base_url_images)
        placeholder = f"__IMAGE_TAG_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # 파일 링크 처리
    def file_handler(match):
        nonlocal counter
        filename = match.group(1)
        text = match.group(2) if match.group(2) else None
        embed_html = _safe_file_link(filename, text, base_url_files)
        placeholder = f"__FILE_LINK_{counter}__"
        counter += 1
        placeholders[placeholder] = embed_html
        return placeholder
    
    # 각 특수 태그 패턴에 핸들러 적용
    content = re.sub(r'\[youtube:([^\]]+)\]', youtube_handler, content)
    content = re.sub(r'\[twitch:([^\]]+)\]', twitch_handler, content)
    content = re.sub(r'\[twitter:([^\]]+)\]', twitter_handler, content)
    content = re.sub(r'\[instagram:([^\]]+)\]', instagram_handler, content)
    content = re.sub(r'\[facebook:([^\]]+)\]', facebook_handler, content)
    content = re.sub(r'\[highlight\](.*?)\[/highlight\]', highlight_handler, content, flags=re.DOTALL)
    content = re.sub(r'\[quote(?:\s+author="([^"]*)")?\](.*?)\[/quote\]', quote_handler, content, flags=re.DOTALL)
    content = re.sub(r'\[img:([^\]]+)(?:\|([^\]]+))?\]', image_handler, content)
    content = re.sub(r'\[file:([^|\]]+)(?:\|([^\]]+))?\]', file_handler, content)
    
    # 2. 텍스트 행 처리 (마크다운 구조 및 일반 텍스트)
    
    # 텍스트 파일 간격 조정을 위한 전처리
    content = re.sub(r'\n\n+', '\n\n', content)  # 빈 줄 정규화
    
    lines = content.split('\n')
    processed_lines = []
    in_code_block = False  # 코드 블록 내부 여부 추적
    empty_line_count = 0   # 연속된 빈 줄 카운트
    
    for line in lines:
        # 플레이스홀더 확인 - 이미 처리된 특수 태그가 있는지
        placeholder_found = any(ph in line for ph in placeholders.keys())
        if placeholder_found:
            # 플레이스홀더가 있는 행은 그대로 유지
            processed_lines.append(line)
            continue
        
        line = line.strip()
        
        # 빈 줄 처리
        if not line:
            empty_line_count += 1
            if empty_line_count == 1:  # 첫 번째 빈 줄만 <br>로 변환
                processed_lines.append('<br>')
            continue
        else:
            empty_line_count = 0
        
        # 코드 블록 처리
        if line.startswith('```'):
            if not in_code_block:
                # 코드 블록 시작
                language = line[3:].strip()
                in_code_block = True
                processed_lines.append(f'<pre><code class="language-{escape(language)}">')
            else:
                # 코드 블록 종료
                in_code_block = False
                processed_lines.append('</code></pre>')
            continue
        
        # 코드 블록 내부의 코드는 구조만 이스케이핑
        if in_code_block:
            processed_lines.append(escape(line))
            continue
        
        # 헤더 처리 (# 시작)
        if line.startswith('#'):
            header_level = len(re.match(r'^#+', line).group(0))
            if header_level > 0 and len(line) > header_level and line[header_level] == ' ':
                header_text = escape(line[header_level+1:].strip())
                processed_lines.append(f'<h{header_level}>{header_text}</h{header_level}>')
                continue
        
        # 목록 처리
        if line.startswith('- ') or line.startswith('* '):
            list_content = escape(line[2:])
            processed_lines.append(f'<li>{list_content}</li>')
            continue
        
        # 번호 목록 처리
        if re.match(r'^\d+\.\s', line):
            match = re.match(r'^\d+\.\s(.+)$', line)
            if match:
                list_content = escape(match.group(1))
                processed_lines.append(f'<li>{list_content}</li>')
                continue
        
        # 수평선 처리
        if line == '---' or line == '***' or line == '___':
            processed_lines.append('<hr>')
            continue
        
        # 일반 텍스트 처리
        processed_lines.append(f'<p class="compact-text">{escape(line)}</p>')
    
    # 3. 모든 라인을 HTML로 결합
    html_content = '\n'.join(processed_lines)
    
    # 4. 플레이스홀더를 실제 HTML로 대체
    for placeholder, embed_html in placeholders.items():
        html_content = html_content.replace(placeholder, embed_html)
    
    # 5. 안전한 HTML로 명시적 표시 (Markup)
    return Markup(html_content)

# 안전한 보조 함수들
def _safe_image_tag(src, alt=None, base_url='/'):
    """안전한 이미지 태그 생성"""
    if not isinstance(src, str) or not src or '..' in src or '/' in src:
        return ""
    
    safe_src = secure_filename(src)
    safe_alt = escape(alt) if alt else escape(safe_src)
    
    return f'<figure class="post-image"><img src="{base_url}/{safe_src}" alt="{safe_alt}" class="text-post-image"><figcaption>{safe_alt if alt else ""}</figcaption></figure>'

def _safe_file_link(filename, text=None, base_url='/'):
    """안전한 파일 링크 생성"""
    if not isinstance(filename, str) or not filename or '..' in filename or '/' in filename:
        return ""
    
    safe_filename = secure_filename(filename)
    safe_text = escape(text) if text else escape(safe_filename)
    
    return f'<a href="{base_url}/{safe_filename}" class="file-download" download><i class="fas fa-download"></i> {safe_text}</a>'

def _create_youtube_embed(youtube_id_or_url):
    """유튜브 임베드 HTML 생성 - 안전하게 처리하고 올바른 HTML 반환"""
    # 안전한 ID 추출
    safe_id = ""
    youtube_id_or_url = str(youtube_id_or_url)  # 입력값 문자열 보장
    
    if 'youtube.com' in youtube_id_or_url or 'youtu.be' in youtube_id_or_url:
        if 'youtube.com/watch' in youtube_id_or_url:
            # https://www.youtube.com/watch?v=VIDEO_ID 형식
            match = re.search(r'v=([^&]+)', youtube_id_or_url)
            if match:
                safe_id = match.group(1)
        elif 'youtu.be/' in youtube_id_or_url:
            # https://youtu.be/VIDEO_ID 형식
            parts = youtube_id_or_url.split('/')
            if len(parts) > 0:
                safe_id = parts[-1]
    else:
        # 이미 ID만 제공된 경우
        safe_id = youtube_id_or_url
    
    # 안전한 ID 이스케이핑 - URL 파라미터용
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 YouTube URL</div>'
    
    # 임베드 HTML 생성 - 반환값은 이미 준비된 HTML이므로 이스케이핑하지 않음
    return f'''
<div class="social-embed youtube-embed">
    <iframe width="880" height="495" src="https://www.youtube.com/embed/{safe_id}" 
    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen></iframe>
</div>
'''

def _create_twitch_embed(twitch_id_or_url):
    """트위치 임베드 HTML 생성 - 안전하게"""
    # 안전한 ID 추출
    safe_id = ""
    twitch_id_or_url = str(twitch_id_or_url)  # 입력값 문자열 보장
    
    if 'twitch.tv' in twitch_id_or_url:
        # https://www.twitch.tv/CHANNEL_ID 형식
        parts = twitch_id_or_url.split('/')
        if len(parts) > 0:
            safe_id = parts[-1]
    else:
        # 이미 ID만 제공된 경우
        safe_id = twitch_id_or_url
    
    # 안전한 ID 이스케이핑 - URL 파라미터용
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Twitch URL</div>'
    
    # 임베드 HTML 생성
    return f'''
<div class="social-embed twitch-embed">
    <iframe src="https://player.twitch.tv/?channel={safe_id}&parent=localhost" 
    frameborder="0" allowfullscreen="true" scrolling="no" height="378" width="620"></iframe>
</div>
'''

def _create_twitter_embed(tweet_id_or_url):
    """트위터 임베드 HTML 생성 - 안전하게"""
    # 안전한 ID 추출
    safe_id = ""
    tweet_id_or_url = str(tweet_id_or_url)  # 입력값 문자열 보장
    
    if 'twitter.com' in tweet_id_or_url or 'x.com' in tweet_id_or_url:
        # https://twitter.com/username/status/TWEET_ID 형식
        parts = tweet_id_or_url.split('/')
        if len(parts) > 0 and 'status' in tweet_id_or_url:
            for i, part in enumerate(parts):
                if part == 'status' and i + 1 < len(parts):
                    safe_id = parts[i+1]
                    break
    else:
        # 이미 ID만 제공된 경우
        safe_id = tweet_id_or_url
    
    # 안전한 ID 이스케이핑 - URL 파라미터용
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Twitter URL</div>'
    
    # 임베드 HTML 생성
    return f'''
<div class="social-embed twitter-embed">
    <blockquote class="twitter-tweet">
        <a href="https://twitter.com/i/status/{safe_id}"></a>
    </blockquote>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</div>
'''

def _create_instagram_embed(post_id_or_url):
    """인스타그램 임베드 HTML 생성 - 안전하게"""
    # 안전한 ID 추출
    safe_id = ""
    post_id_or_url = str(post_id_or_url)  # 입력값 문자열 보장
    
    if 'instagram.com' in post_id_or_url:
        # https://www.instagram.com/p/POST_ID/ 형식
        match = re.search(r'instagram\.com/p/([^/]+)', post_id_or_url)
        if match:
            safe_id = match.group(1)
    else:
        # 이미 ID만 제공된 경우
        safe_id = post_id_or_url
    
    # 안전한 ID 이스케이핑 - URL 파라미터용
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Instagram URL</div>'
    
    # 임베드 HTML 생성
    return f'''
<div class="social-embed instagram-embed">
    <blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/{safe_id}/">
        <a href="https://www.instagram.com/p/{safe_id}/"></a>
    </blockquote>
    <script async src="//www.instagram.com/embed.js"></script>
</div>
'''

def _create_facebook_embed(post_url):
    """페이스북 임베드 HTML 생성 - 안전하게"""
    # 안전한 URL 이스케이핑 - URL 파라미터용
    post_url = str(post_url)  # 입력값 문자열 보장
    safe_url = escape(post_url)
    
    if 'facebook.com' not in safe_url:
        return '<div class="error-embed">잘못된 Facebook URL</div>'
    
    # 임베드 HTML 생성
    return f'''
<div class="social-embed facebook-embed">
    <div class="fb-post" data-href="{safe_url}"></div>
    <div id="fb-root"></div>
    <script async defer src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v3.2"></script>
</div>
'''

def _create_highlight_box(content):
    """강조 내용 박스 생성 - 안전하게"""
    if not isinstance(content, str):
        return ""
    
    return f'<div class="highlight-box">{content}</div>'

def _create_quote_box(content, author=None):
    """인용문 박스 생성 - 안전하게"""
    if not isinstance(content, str):
        return ""
    
    author_html = f'<span class="blockquote-author">{author}</span>' if author else ''
    return f'<blockquote class="styled-quote">{content}{author_html}</blockquote>'

def get_text_post(text_dir, filename):
    """특정 텍스트 파일 로드하여 TextPost 객체 반환 - 보안 강화"""
    # 경로 및 파일명 검증
    if not isinstance(text_dir, str) or not isinstance(filename, str):
        return None
        
    if '..' in filename or '/' in filename or '\\' in filename:
        return None
        
    # 파일명 정규화
    safe_filename = secure_filename(filename)
    if safe_filename != filename:
        return None
    
    try:
        # 경로 정규화 및 검증
        file_path = os.path.join(text_dir, safe_filename)
        abs_path = os.path.abspath(file_path)
        
        # 기본 디렉토리 외부 접근 시도 방지
        if not abs_path.startswith(os.path.abspath(text_dir)):
            return None
            
        # 파일 존재 확인
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return None
            
        # 파일 확장자 확인
        if not abs_path.endswith('.txt'):
            return None
            
        # 파일 크기 제한 (5MB)
        if os.path.getsize(abs_path) > 5 * 1024 * 1024:
            return None
            
        # 파일 파싱
        metadata, content = parse_text_file(abs_path)
        
        # TextPost 객체 생성 및 반환
        return TextPost(safe_filename, content, metadata)
        
    except Exception as e:
        print(f"텍스트 포스트 로드 오류: {str(e)}")
    
    return None

def get_all_text_posts(text_dir, tag=None):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환 - 보안 강화"""
    posts = []
    
    # 경로 검증
    if not isinstance(text_dir, str):
        return posts
        
    # 태그 검증
    if tag is not None and (not isinstance(tag, str) or len(tag) > 50):
        return posts
    
    try:
        # 디렉토리 존재 확인
        if not os.path.exists(text_dir) or not os.path.isdir(text_dir):
            return posts
            
        # 디렉토리 내 파일 목록 가져오기
        filenames = []
        try:
            filenames = os.listdir(text_dir)
        except Exception:
            return posts
            
        # 파일 수 제한 (최대 1000개)
        filenames = filenames[:1000]
        
        for filename in filenames:
            if filename.endswith('.txt'):
                # 안전한 방식으로 TextPost 객체 가져오기
                post = get_text_post(text_dir, filename)
                
                if post:
                    # 태그 필터링
                    if tag is None or tag in post.tags:
                        posts.append(post)
    except Exception as e:
        print(f"텍스트 포스트 로드 오류: {str(e)}")
    
    # 날짜순 정렬 (최신순)
    posts.sort(key=lambda x: x.date, reverse=True)
    return posts

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
    
    # 검색어 검증
    if not isinstance(query, str) or len(query) > 100:
        return []
        
    # 검색어 이스케이핑 - 비교용
    query = escape(query).lower()
    results = []
    
    all_posts = get_all_text_posts(text_dir)
    for post in all_posts:
        # 제목, 내용, 태그에서 검색
        if (query in post.title.lower() or 
            query in post.content.lower() or 
            any(query in tag.lower() for tag in post.tags)):
            results.append(post)
    
    return results


def get_series_posts(text_dir, series_name):
    """시리즈에 속한 모든 포스트 검색"""
    # 시리즈명 검증
    if not isinstance(series_name, str) or len(series_name) > 100:
        return []
        
    series_posts = []
    
    try:
        all_posts = get_all_text_posts(text_dir)
        
        # 같은 시리즈에 속한 포스트 필터링
        for post in all_posts:
            if hasattr(post, 'series') and post.series == series_name:
                series_posts.append(post)
        
        # 시리즈 파트 순서대로 정렬
        series_posts.sort(key=lambda x: x.series_part if x.series_part is not None else 9999)
        
    except Exception as e:
        print(f"시리즈 포스트 로드 오류: {str(e)}")
    
    return series_posts

def get_adjacent_posts(text_dir, current_post):
    """현재 포스트의 이전 및 다음 포스트 반환"""
    # 포스트 검증
    if not current_post or not isinstance(current_post, TextPost):
        return None, None
        
    try:
        all_posts = get_all_text_posts(text_dir)
        
        # 날짜순으로 정렬 (최신순)
        all_posts.sort(key=lambda x: x.date, reverse=True)
        
        current_index = None
        for i, post in enumerate(all_posts):
            if post.id == current_post.id:
                current_index = i
                break
        
        if current_index is None:
            return None, None
        
        # 이전 포스트 (더 최신 게시물)
        prev_post = all_posts[current_index - 1] if current_index > 0 else None
        
        # 다음 포스트 (더 오래된 게시물)
        next_post = all_posts[current_index + 1] if current_index < len(all_posts) - 1 else None
        
        return prev_post, next_post
    except Exception as e:
        print(f"이전/다음 포스트 조회 오류: {str(e)}")
        return None, None