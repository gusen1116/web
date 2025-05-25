# app/services/text_service.py
import os
import re
from datetime import datetime
from flask import url_for, current_app
from markupsafe import escape, Markup
from werkzeug.utils import secure_filename

# 마크다운 처리를 위한 임포트
try:
    import markdown
    import bleach
    MARKDOWN_ENABLED = True
except ImportError:
    MARKDOWN_ENABLED = False
    print("markdown 또는 bleach 라이브러리가 설치되지 않았습니다. 기본 텍스트 처리 방식을 사용합니다.")

class TextPost:
    """텍스트 파일 기반 포스트 클래스 - 설명 위치 개선"""
    
    def __init__(self, filename, content, metadata=None):
        # 파일명 검증 - 한글 지원을 위해 더 유연하게 수정
        if not isinstance(filename, str) or '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("잘못된 파일명입니다")
            
        self.filename = filename  # secure_filename 제거하여 한글 파일명 지원
        self.content = content
        self.id = os.path.splitext(self.filename)[0]
        
        # 메타데이터 기본값
        self.title = self.filename
        self.date = datetime.now()
        self.created_at = datetime.now()
        self.tags = []
        self.author = "구센"
        self.description = ""  # 짧은 설명
        self.subtitle = ""     # 부제목 (제목 아래 표시용)
        self.slug = None
        self.series = None
        self.series_part = None
        self.changelog = []
        
        # 메타데이터가 제공된 경우 안전하게 업데이트
        if metadata:
            # 기본 필드들
            if 'title' in metadata and isinstance(metadata['title'], str):
                self.title = escape(metadata['title'])
                
            if 'description' in metadata and isinstance(metadata['description'], str):
                self.description = escape(metadata['description'])
                
            if 'subtitle' in metadata and isinstance(metadata['subtitle'], str):
                self.subtitle = escape(metadata['subtitle'])
                
            if 'author' in metadata and isinstance(metadata['author'], str):
                self.author = escape(metadata['author'])
                
            # 슬러그 설정 및 검증 - 한글도 지원하도록 수정
            if 'slug' in metadata and isinstance(metadata['slug'], str):
                # 위험한 문자만 제거하고 한글은 유지
                clean_slug = metadata['slug']
                if not ('..' in clean_slug or '/' in clean_slug or '\\' in clean_slug):
                    self.slug = clean_slug
                else:
                    self.slug = self.id
            else:
                self.slug = self.id
            
            # 날짜 파싱
            date_str = metadata.get('date')
            if date_str and isinstance(date_str, str):
                try:
                    self.date = datetime.strptime(date_str, '%Y-%m-%d')
                    self.created_at = self.date
                except ValueError:
                    pass
            
            # 태그 파싱
            tags_str = metadata.get('tags')
            if tags_str and isinstance(tags_str, str):
                clean_tags = []
                for tag in tags_str.split(','):
                    clean_tag = tag.strip()
                    if clean_tag and len(clean_tag) <= 50:
                        clean_tags.append(escape(clean_tag))
                self.tags = clean_tags
            
            # 시리즈 정보 파싱
            series_str = metadata.get('series')
            if series_str and isinstance(series_str, str):
                self.series = escape(series_str)
            
            series_part_str = metadata.get('series-part')
            if series_part_str and isinstance(series_part_str, str):
                try:
                    part = int(series_part_str)
                    if 0 < part < 1000:
                        self.series_part = part
                    else:
                        self.series_part = 1
                except ValueError:
                    self.series_part = 1
            
            # 수정 이력 파싱
            changelog_str = metadata.get('changelog')
            if changelog_str and isinstance(changelog_str, str):
                clean_logs = []
                for item in changelog_str.split(','):
                    clean_item = item.strip()
                    if clean_item and len(clean_item) <= 200:
                        clean_logs.append(escape(clean_item))
                self.changelog = clean_logs
    
    def get_url(self):
        """포스트 URL 반환"""
        if hasattr(self, 'slug') and self.slug:
            return url_for('posts.view_by_slug', slug=self.slug)
        return url_for('posts.view_by_slug', slug=self.id)

    def get_preview(self, length=200):
        """본문 미리보기 생성 - 항상 본문에서 추출"""
        if not isinstance(length, int) or length <= 0 or length > 1000:
            length = 200
            
        # 항상 본문에서 미리보기 생성 (description 무시)
        text = self.content
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
        """글자 수 반환"""
        text = self.content
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
            r'\[pullquote.*?\].*?\[/pullquote\]',
            r'\[gallery\].*?\[/gallery\]',
            r'\[related\].*?\[/related\]',
            r'\[changelog\].*?\[/changelog\]',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL)
        
        try:
            words = re.findall(r'\w+', text)
            return min(len(words), 100000)
        except Exception:
            return 0


def get_content_dir():
    """컨텐츠 디렉토리 경로 반환"""
    return current_app.config.get('CONTENT_FOLDER', os.path.join(current_app.root_path, 'static', 'content'))

def get_posts_dir():
    """포스트 디렉토리 경로 반환"""
    return os.path.join(get_content_dir(), 'posts')

def get_media_dir():
    """미디어 디렉토리 경로 반환"""
    return os.path.join(get_content_dir(), 'media')

def parse_text_file(file_path):
    """텍스트 파일 파싱하여 메타데이터와 본문 분리"""
    if not isinstance(file_path, str):
        return {}, ""
        
    abs_path = os.path.abspath(file_path)
    if '..' in file_path or not abs_path.endswith('.txt'):
        return {}, ""
    
    try:
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
                if isinstance(key, str) and isinstance(value, str) and len(key) <= 50 and len(value) <= 500:
                    metadata[key.lower()] = value
                content_start = i + 1
            else:
                break
        
        # 본문 추출
        body_content = '\n'.join(content_lines[content_start:])
        
        return metadata, body_content
    
    except Exception as e:
        print(f"텍스트 파일 파싱 오류: {str(e)}")
        return {}, ""


def render_content(content, base_url_images='/static/content/media', base_url_videos='/static/content/media', base_url_audios='/static/content/media'):
    """
    특수 태그를 HTML로 변환 후 마크다운 처리 및 URL 자동 링크 변환
    
    이 함수는 여러 단계로 텍스트를 처리합니다:
    1. 특수 태그 ([img:], [video:] 등) 처리
    2. 마크다운 문법을 HTML로 변환
    3. 일반 URL을 자동으로 클릭 가능한 링크로 변환 (새로 추가된 기능)
    4. 보안을 위한 HTML 정리
    """
    if not isinstance(content, str):
        return ""
    
    # URL 검증 - 보안을 위해 모든 URL이 /로 시작하는지 확인
    if not isinstance(base_url_images, str) or not base_url_images.startswith('/'):
        base_url_images = '/static/content/media'
    if not isinstance(base_url_videos, str) or not base_url_videos.startswith('/'):
        base_url_videos = '/static/content/media'
    if not isinstance(base_url_audios, str) or not base_url_audios.startswith('/'):
        base_url_audios = '/static/content/media'
    
    # 특수 태그 처리 함수들
    def youtube_handler(match):
        youtube_id_or_url = match.group(1)
        return _create_youtube_embed(youtube_id_or_url)
    
    def twitch_handler(match):
        twitch_id_or_url = match.group(1)
        return _create_twitch_embed(twitch_id_or_url)
    
    def twitter_handler(match):
        tweet_id_or_url = match.group(1)
        return _create_twitter_embed(tweet_id_or_url)
    
    def instagram_handler(match):
        post_id_or_url = match.group(1)
        return _create_instagram_embed(post_id_or_url)
    
    def facebook_handler(match):
        post_url = match.group(1)
        return _create_facebook_embed(post_url)
    
    def highlight_handler(match):
        highlight_content = match.group(1)
        safe_content = escape(highlight_content)
        return _create_highlight_box(safe_content)
    
    def quote_handler(match):
        author = match.group(1)
        quote_content = match.group(2)
        safe_content = escape(quote_content)
        safe_author = escape(author) if author else None
        return _create_quote_box(safe_content, safe_author)
    
    def image_handler(match):
        src = match.group(1)
        alt = match.group(2) if match.group(2) else None
        return _safe_image_tag(src, alt, base_url_images)
    
    def video_handler(match):
        filename = match.group(1)
        caption = match.group(2) if match.group(2) else None
        return _create_video_embed(filename, caption, base_url_videos)
    
    def audio_handler(match):
        filename = match.group(1)
        caption = match.group(2) if match.group(2) else None
        return _create_audio_embed(filename, caption, base_url_audios)
    
    # 1단계: 특수 태그 변환 - 사용자 정의 태그를 HTML로 변환
    content = re.sub(r'\[youtube:([^\]]+)\]', youtube_handler, content)
    content = re.sub(r'\[twitch:([^\]]+)\]', twitch_handler, content)
    content = re.sub(r'\[twitter:([^\]]+)\]', twitter_handler, content)
    content = re.sub(r'\[instagram:([^\]]+)\]', instagram_handler, content)
    content = re.sub(r'\[facebook:([^\]]+)\]', facebook_handler, content)
    content = re.sub(r'\[highlight\](.*?)\[/highlight\]', highlight_handler, content, flags=re.DOTALL)
    content = re.sub(r'\[quote(?:\s+author="([^"]*)")?\](.*?)\[/quote\]', quote_handler, content, flags=re.DOTALL)
    content = re.sub(r'\[img:([^\]]+)(?:\|([^\]]+))?\]', image_handler, content)
    content = re.sub(r'\[video:([^\]]+)(?:\|([^\]]+))?\]', video_handler, content)
    content = re.sub(r'\[audio:([^\]]+)(?:\|([^\]]+))?\]', audio_handler, content)
    
    # 2단계: 마크다운 처리 - 표준 마크다운 문법을 HTML로 변환
    if MARKDOWN_ENABLED:
        try:
            extensions = ['extra', 'nl2br', 'sane_lists']
            extension_configs = {
                'nl2br': {},
                'extra': {},
                'sane_lists': {}
            }
            
            md_content = markdown.markdown(content, extensions=extensions, extension_configs=extension_configs)
            
            # 허용된 HTML 태그 정의 - 보안을 위해 제한적으로 허용
            allowed_tags = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'hr', 
                'a', 'strong', 'em', 'code', 'pre', 'blockquote', 'img',
                'ul', 'ol', 'li', 'span', 'div', 'iframe', 'figure', 'figcaption',
                'video', 'audio', 'source'
            ]
            allowed_attrs = {
                'a': ['href', 'title', 'target', 'rel', 'class'],
                'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
                'p': ['class'],
                'div': ['class'],
                'span': ['class'],
                'code': ['class'],
                'pre': ['class'],
                'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow'],
                'figure': ['class'],
                'figcaption': ['class'],
                'video': ['controls', 'width', 'height', 'class'],
                'audio': ['controls', 'class'],
                'source': ['src', 'type']
            }
            
            cleaned_content = bleach.clean(md_content, tags=allowed_tags, attributes=allowed_attrs)
            cleaned_content = cleaned_content.replace('<p>', '<p class="compact-text">')
            
        except Exception as e:
            print(f"마크다운 처리 오류, 기존 방식으로 대체: {str(e)}")
            cleaned_content = _process_content_legacy(content)
    else:
        cleaned_content = _process_content_legacy(content)
    
    # 3단계: URL 자동 링크 변환 추가 - 마크다운 처리 후에 실행
    # 이 단계에서 일반 URL들이 클릭 가능한 링크로 변환됩니다
    cleaned_content = _auto_linkify_urls(cleaned_content)
    
    return Markup(cleaned_content)


def _auto_linkify_urls(text):
    """
    텍스트 내의 일반 URL을 자동으로 클릭 가능한 링크로 변환하는 함수
    
    이 함수는 정규식의 lookbehind 제한 문제를 해결하기 위해
    단순하지만 효과적인 접근 방식을 사용합니다.
    
    작동 원리:
    1. 고정 폭 lookbehind만 사용하여 Python 정규식 제한을 우회
    2. href= 또는 src= 바로 뒤에 오는 URL은 제외 (이미 HTML 속성 안에 있는 URL)
    3. 찾은 URL을 안전한 <a> 태그로 감싸기
    4. 보안을 위해 target="_blank"와 rel="noopener noreferrer" 속성 추가
    """
    if not isinstance(text, str):
        return text
    
    # 간단하고 안정적인 URL 패턴 사용
    # 고정 폭 lookbehind만 사용하여 Python 정규식 제한을 피합니다
    url_pattern = re.compile(
        r'(?<!href=")(?<!src=")'  # 고정 폭 lookbehind: HTML 속성 안의 URL 제외
        r'(https?://[^\s<>"\']+)',  # 실제 URL 패턴 매칭
        re.IGNORECASE
    )
    
    def url_replacer(match):
        """
        각각의 URL을 안전한 링크로 변환하는 내부 함수
        
        이 함수는 다음 작업을 수행합니다:
        1. URL 끝의 문장부호 제거 (자연스러운 텍스트 처리)
        2. 보안을 위한 URL 이스케이핑
        3. 긴 URL 축약하여 표시
        4. 안전한 외부 링크 태그 생성
        """
        url = match.group(1)
        
        # URL 끝의 문장부호 제거 - 자연스러운 텍스트 처리를 위해
        # 예: "https://example.com." → "https://example.com"
        url = url.rstrip('.,;:!?')
        
        # 보안을 위한 URL 이스케이핑 - XSS 공격 방지
        safe_url = escape(url)
        
        # 표시할 텍스트 생성 - 너무 긴 URL은 축약하여 가독성 향상
        if len(url) > 60:
            display_text = url[:57] + "..."
        else:
            display_text = url
        
        # 안전한 링크 태그 생성
        # target="_blank": 새 탭에서 열기
        # rel="noopener noreferrer": 보안을 위한 속성
        # class="auto-link": CSS 스타일링을 위한 클래스
        return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="auto-link">{escape(display_text)}</a>'
    
    # URL을 링크로 변환하여 반환
    return url_pattern.sub(url_replacer, text)


# ===== 헬퍼 함수들 - 각 미디어 타입별 HTML 생성 =====

def _create_youtube_embed(youtube_id_or_url):
    """유튜브 임베드 HTML 생성"""
    safe_id = ""
    youtube_id_or_url = str(youtube_id_or_url)
    
    if 'youtube.com' in youtube_id_or_url or 'youtu.be' in youtube_id_or_url:
        if 'youtube.com/watch' in youtube_id_or_url:
            match = re.search(r'v=([^&]+)', youtube_id_or_url)
            if match:
                safe_id = match.group(1)
        elif 'youtu.be/' in youtube_id_or_url:
            parts = youtube_id_or_url.split('/')
            if len(parts) > 0:
                safe_id = parts[-1]
    else:
        safe_id = youtube_id_or_url
    
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 YouTube URL</div>'
    
    return f'''
<div class="social-embed youtube-embed">
    <iframe src="https://www.youtube.com/embed/{safe_id}" 
    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen></iframe>
</div>
'''

def _create_twitch_embed(twitch_id_or_url):
    """트위치 임베드 HTML 생성"""
    safe_id = ""
    twitch_id_or_url = str(twitch_id_or_url)
    
    if 'twitch.tv' in twitch_id_or_url:
        parts = twitch_id_or_url.split('/')
        if len(parts) > 0:
            safe_id = parts[-1]
    else:
        safe_id = twitch_id_or_url
    
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Twitch URL</div>'
    
    return f'''
<div class="social-embed twitch-embed">
    <iframe src="https://player.twitch.tv/?channel={safe_id}&parent=localhost" 
    frameborder="0" allowfullscreen="true" scrolling="no"></iframe>
</div>
'''

def _create_twitter_embed(tweet_id_or_url):
    """트위터 임베드 HTML 생성"""
    safe_id = ""
    tweet_id_or_url = str(tweet_id_or_url)
    
    if 'twitter.com' in tweet_id_or_url or 'x.com' in tweet_id_or_url:
        parts = tweet_id_or_url.split('/')
        if len(parts) > 0 and 'status' in tweet_id_or_url:
            for i, part in enumerate(parts):
                if part == 'status' and i + 1 < len(parts):
                    safe_id = parts[i+1]
                    break
    else:
        safe_id = tweet_id_or_url
    
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Twitter URL</div>'
    
    return f'''
<div class="social-embed twitter-embed">
    <blockquote class="twitter-tweet">
        <a href="https://twitter.com/i/status/{safe_id}"></a>
    </blockquote>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</div>
'''

def _create_instagram_embed(post_id_or_url):
    """인스타그램 임베드 HTML 생성"""
    safe_id = ""
    post_id_or_url = str(post_id_or_url)
    
    if 'instagram.com' in post_id_or_url:
        match = re.search(r'instagram\.com/p/([^/]+)', post_id_or_url)
        if match:
            safe_id = match.group(1)
    else:
        safe_id = post_id_or_url
    
    safe_id = escape(safe_id)
    
    if not safe_id:
        return '<div class="error-embed">잘못된 Instagram URL</div>'
    
    return f'''
<div class="social-embed instagram-embed">
    <blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/p/{safe_id}/">
        <a href="https://www.instagram.com/p/{safe_id}/"></a>
    </blockquote>
    <script async src="//www.instagram.com/embed.js"></script>
</div>
'''

def _create_facebook_embed(post_url):
    """페이스북 임베드 HTML 생성"""
    post_url = str(post_url)
    safe_url = escape(post_url)
    
    if 'facebook.com' not in safe_url:
        return '<div class="error-embed">잘못된 Facebook URL</div>'
    
    return f'''
<div class="social-embed facebook-embed">
    <div class="fb-post" data-href="{safe_url}"></div>
    <div id="fb-root"></div>
    <script async defer src="https://connect.facebook.net/ko_KR/sdk.js#xfbml=1&version=v16.0"></script>
</div>
'''

def _safe_image_tag(src, alt=None, base_url='/'):
    """안전한 이미지 태그 생성 - 한글 파일명 지원"""
    if not isinstance(src, str) or not src or '..' in src or '/' in src:
        return '<div class="error-embed">잘못된 이미지 경로</div>'
    
    # secure_filename 대신 위험한 문자만 체크
    if any(char in src for char in ['<', '>', '"', "'"]):
        return '<div class="error-embed">잘못된 이미지 경로</div>'
    
    safe_alt = escape(alt) if alt else escape(src)
    
    return f'''
<figure class="post-image">
    <img src="{base_url}/{src}" alt="{safe_alt}" class="text-post-image">
    {f'<figcaption>{safe_alt}</figcaption>' if alt else ''}
</figure>
'''

def _create_video_embed(video_filename, caption=None, base_url='/'):
    """비디오 임베드 HTML 생성 - 한글 파일명 지원"""
    if not isinstance(video_filename, str) or not video_filename or '..' in video_filename or '/' in video_filename:
        return '<div class="error-embed">잘못된 비디오 파일명</div>'
    
    # 위험한 문자만 체크
    if any(char in video_filename for char in ['<', '>', '"', "'"]):
        return '<div class="error-embed">잘못된 비디오 파일명</div>'
    
    safe_caption = escape(caption) if caption else escape(video_filename)
    
    file_ext = video_filename.rsplit('.', 1)[1].lower() if '.' in video_filename else ''
    mime_type = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'ogg': 'video/ogg',
        'mov': 'video/quicktime'
    }.get(file_ext, 'video/mp4')
    
    return f'''
<div class="video-embed">
    <video controls width="100%">
        <source src="{base_url}/{video_filename}" type="{mime_type}">
        브라우저가 비디오 재생을 지원하지 않습니다.
    </video>
    {f'<figcaption>{safe_caption}</figcaption>' if caption else ''}
</div>
'''

def _create_audio_embed(audio_filename, caption=None, base_url='/'):
    """오디오 임베드 HTML 생성 - 한글 파일명 지원"""
    if not isinstance(audio_filename, str) or not audio_filename or '..' in audio_filename or '/' in audio_filename:
        return '<div class="error-embed">잘못된 오디오 파일명</div>'
    
    # 위험한 문자만 체크
    if any(char in audio_filename for char in ['<', '>', '"', "'"]):
        return '<div class="error-embed">잘못된 오디오 파일명</div>'
    
    safe_caption = escape(caption) if caption else escape(audio_filename)
    
    file_ext = audio_filename.rsplit('.', 1)[1].lower() if '.' in audio_filename else ''
    mime_type = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'm4a': 'audio/mp4'
    }.get(file_ext, 'audio/mpeg')
    
    return f'''
<div class="audio-embed">
    <audio controls style="width:100%">
        <source src="{base_url}/{audio_filename}" type="{mime_type}">
        브라우저가 오디오 재생을 지원하지 않습니다.
    </audio>
    {f'<div class="audio-caption">{safe_caption}</div>' if caption else ''}
</div>
'''

def _create_highlight_box(content):
    """강조 내용 박스 생성"""
    if not isinstance(content, str):
        return ""
    return f'<div class="highlight-box">{content}</div>'

def _create_quote_box(content, author=None):
    """인용문 박스 생성"""
    if not isinstance(content, str):
        return ""
    author_html = f'<span class="blockquote-author">{author}</span>' if author else ''
    return f'<blockquote class="styled-quote">{content}{author_html}</blockquote>'

def _process_content_legacy(content):
    """
    기존 방식으로 텍스트 처리 (마크다운 라이브러리 없을 때 사용)
    
    이 함수는 마크다운 라이브러리가 설치되지 않은 환경에서
    기본적인 텍스트 처리를 담당합니다. 마크다운 처리 후에도
    URL 자동 링크 변환이 적용되도록 수정되었습니다.
    """
    lines = content.split('\n')
    processed_lines = []
    in_code_block = False
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                # URL 자동 링크 변환 적용 - 이 부분이 새로 추가되었습니다
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            processed_lines.append('<br>')
            continue
        
        if line.startswith('```'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                # URL 자동 링크 변환 적용
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
                
            if not in_code_block:
                language = line[3:].strip()
                in_code_block = True
                processed_lines.append(f'<pre><code class="language-{escape(language)}">')
            else:
                in_code_block = False
                processed_lines.append('</code></pre>')
            continue
        
        if in_code_block:
            processed_lines.append(escape(line))
            continue
        
        if line.startswith('#'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                # URL 자동 링크 변환 적용
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
                
            header_level = len(re.match(r'^#+', line).group(0))
            if header_level > 0 and len(line) > header_level and line[header_level] == ' ':
                header_text = escape(line[header_level+1:].strip())
                processed_lines.append(f'<h{header_level}>{header_text}</h{header_level}>')
                continue
        
        current_paragraph.append(escape(line))
    
    if current_paragraph:
        paragraph_text = " ".join(current_paragraph)
        # URL 자동 링크 변환 적용
        paragraph_text = _auto_linkify_urls(paragraph_text)
        processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
    
    return '\n'.join(processed_lines)


# ===== 포스트 관리 함수들 =====

def get_all_text_posts(posts_dir=None, tag=None):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환"""
    if posts_dir is None:
        posts_dir = get_posts_dir()
        
    posts = []
    
    if not isinstance(posts_dir, str):
        return posts
        
    if tag is not None and (not isinstance(tag, str) or len(tag) > 50):
        return posts
    
    try:
        if not os.path.exists(posts_dir) or not os.path.isdir(posts_dir):
            return posts
            
        filenames = []
        try:
            filenames = os.listdir(posts_dir)
        except Exception:
            return posts
            
        filenames = filenames[:1000]  # 제한
        
        for filename in filenames:
            if filename.endswith('.txt'):
                post = get_text_post(posts_dir, filename)
                
                if post:
                    if tag is None or tag in post.tags:
                        posts.append(post)
    except Exception as e:
        print(f"텍스트 포스트 로드 오류: {str(e)}")
    
    posts.sort(key=lambda x: x.date, reverse=True)
    return posts

def get_text_post(posts_dir, filename):
    """특정 텍스트 파일 로드하여 TextPost 객체 반환 - 한글 파일명 지원"""
    
    # 기본 타입 검증
    if not isinstance(posts_dir, str) or not isinstance(filename, str):
        return None
    
    # 파일명 길이 제한 (너무 긴 파일명 방지)
    if len(filename) > 255:
        return None
    
    # 경로 조작 방지를 위한 위험한 문자 검사
    dangerous_patterns = ['..', '/', '\\', '\x00']  # null byte 포함
    for pattern in dangerous_patterns:
        if pattern in filename:
            return None
    
    # 숨김 파일 검사 (점으로 시작하는 파일 차단)
    if filename.startswith('.'):
        return None
    
    # 텍스트 파일만 허용 (.txt 확장자 검증)
    if not filename.lower().endswith('.txt'):
        return None
    
    # 제어 문자 검사 (ASCII 제어 문자들 차단)
    if any(ord(char) < 32 for char in filename if ord(char) < 127):
        return None
    
    # 파일명에 인쇄 불가능한 문자가 있는지 검사
    try:
        # 파일명이 유효한 유니코드인지 확인
        filename.encode('utf-8').decode('utf-8')
    except UnicodeError:
        return None
    
    try:
        # 파일 경로 구성
        file_path = os.path.join(posts_dir, filename)
        abs_path = os.path.abspath(file_path)
        
        # 경로가 지정된 디렉토리 내부에 있는지 확인 (디렉토리 트래버설 방지)
        if not abs_path.startswith(os.path.abspath(posts_dir)):
            return None
            
        # 파일 존재 여부 및 타입 확인
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return None
        
        # 파일 크기 제한 (5MB 초과 시 차단)
        if os.path.getsize(abs_path) > 5 * 1024 * 1024:
            return None
        
        # 파일 읽기 권한 확인
        if not os.access(abs_path, os.R_OK):
            return None
            
        # 메타데이터와 본문 파싱
        metadata, content = parse_text_file(abs_path)
        
        # TextPost 객체 생성 및 반환
        return TextPost(filename, content, metadata)
        
    except Exception as e:
        # 예외 발생 시 로그 출력 (디버깅용)
        print(f"텍스트 포스트 로드 오류 (파일: {filename}): {str(e)}")
        return None

def get_tags_count(posts_dir=None):
    """모든 텍스트 파일의 태그 카운트 반환"""
    if posts_dir is None:
        posts_dir = get_posts_dir()
        
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
        print(f"태그 카운트 오류: {str(e)}")
    
    return tags_count

def get_series_posts(posts_dir, series_name):
    """시리즈에 속한 모든 포스트 검색"""
    if not isinstance(series_name, str) or len(series_name) > 100:
        return []
        
    series_posts = []
    
    try:
        all_posts = get_all_text_posts(posts_dir)
        
        for post in all_posts:
            if hasattr(post, 'series') and post.series == series_name:
                series_posts.append(post)
        
        # 시리즈 파트 순서대로 정렬
        series_posts.sort(key=lambda x: x.series_part if x.series_part is not None else 9999)
        
    except Exception as e:
        print(f"시리즈 포스트 로드 오류: {str(e)}")
    
    return series_posts

def get_adjacent_posts(posts_dir, current_post):
    """현재 포스트의 이전 및 다음 포스트 반환"""
    if not current_post or not isinstance(current_post, TextPost):
        return None, None
        
    try:
        all_posts = get_all_text_posts(posts_dir)
        
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

def search_posts(posts_dir, query):
    """포스트 검색"""
    if not query:
        return []
    
    if not isinstance(query, str) or len(query) > 100:
        return []
        
    query = escape(query).lower()
    results = []
    
    all_posts = get_all_text_posts(posts_dir)
    for post in all_posts:
        # 제목, 내용, 태그, 설명에서 검색
        if (query in post.title.lower() or 
            query in post.content.lower() or
            query in post.description.lower() or
            any(query in tag.lower() for tag in post.tags)):
            results.append(post)
    
    return results