# app/services/text_service.py
import os
import re
import time
from datetime import datetime
from flask import url_for, current_app
from markupsafe import escape, Markup

# 마크다운 처리를 위한 임포트
try:
    import markdown
    import bleach
    MARKDOWN_ENABLED = True
except ImportError:
    MARKDOWN_ENABLED = False

# 캐싱 변수
_posts_cache = None
_cache_timestamp = None
_tags_cache = None

class TextPost:
    """텍스트 파일 기반 포스트 클래스"""
    
    def __init__(self, filename, content, metadata=None):
        # 파일명 검증
        if not isinstance(filename, str) or '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("잘못된 파일명입니다")
            
        self.filename = filename
        self.content = content
        self.id = os.path.splitext(self.filename)[0]
        
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
    
    def _update_metadata(self, metadata):
        """메타데이터 안전하게 업데이트"""
        # 기본 필드들
        if 'title' in metadata and isinstance(metadata['title'], str):
            self.title = escape(metadata['title'])
            
        if 'description' in metadata and isinstance(metadata['description'], str):
            self.description = escape(metadata['description'])
            
        if 'subtitle' in metadata and isinstance(metadata['subtitle'], str):
            self.subtitle = escape(metadata['subtitle'])
            
        if 'author' in metadata and isinstance(metadata['author'], str):
            self.author = escape(metadata['author'])
            
        # 슬러그 설정
        if 'slug' in metadata and isinstance(metadata['slug'], str):
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
        
        # 시리즈 정보
        series_str = metadata.get('series')
        if series_str and isinstance(series_str, str):
            self.series = escape(series_str)
        
        series_part_str = metadata.get('series-part')
        if series_part_str and isinstance(series_part_str, str):
            try:
                part = int(series_part_str)
                if 0 < part < 1000:
                    self.series_part = part
            except ValueError:
                self.series_part = 1
        
        # 수정 이력
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
        """본문 미리보기 생성"""
        if not isinstance(length, int) or length <= 0 or length > 1000:
            length = 200
            
        text = self.content
        # 특수 태그 제거
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
        
        # 길이 제한
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
        current_app.logger.error(f"텍스트 파일 파싱 오류: {str(e)}")
        return {}, ""


def get_all_text_posts(posts_dir=None, tag=None):
    """모든 텍스트 파일 로드하여 TextPost 객체 목록 반환 - 캐싱 적용"""
    global _posts_cache, _cache_timestamp
    
    if posts_dir is None:
        posts_dir = current_app.config.get('POSTS_DIR')
    
    # 캐시 확인
    cache_timeout = current_app.config.get('CACHE_TIMEOUT', 300)
    if _posts_cache and _cache_timestamp and (time.time() - _cache_timestamp < cache_timeout):
        # 캐시된 데이터 사용
        if tag:
            return [p for p in _posts_cache if tag in p.tags]
        return _posts_cache[:]
    
    # 캐시 갱신
    posts = []
    
    try:
        if not os.path.exists(posts_dir) or not os.path.isdir(posts_dir):
            return posts
            
        filenames = os.listdir(posts_dir)
        filenames = filenames[:1000]  # 제한
        
        for filename in filenames:
            if filename.endswith('.txt'):
                post = get_text_post(posts_dir, filename)
                if post:
                    posts.append(post)
    except Exception as e:
        current_app.logger.error(f"텍스트 포스트 로드 오류: {str(e)}")
    
    # 날짜순 정렬
    posts.sort(key=lambda x: x.date, reverse=True)
    
    # 캐시 저장
    _posts_cache = posts
    _cache_timestamp = time.time()
    
    # 태그 필터링
    if tag:
        return [p for p in posts if tag in p.tags]
    
    return posts[:]


def get_text_post(posts_dir, filename):
    """특정 텍스트 파일 로드하여 TextPost 객체 반환"""
    # 캐시에서 먼저 찾기
    if _posts_cache:
        for post in _posts_cache:
            if post.filename == filename:
                return post
    
    # 파일명 검증
    if not isinstance(posts_dir, str) or not isinstance(filename, str):
        return None
    
    if len(filename) > 255:
        return None
    
    dangerous_patterns = ['..', '/', '\\', '\x00']
    for pattern in dangerous_patterns:
        if pattern in filename:
            return None
    
    if filename.startswith('.'):
        return None
    
    if not filename.lower().endswith('.txt'):
        return None
    
    try:
        file_path = os.path.join(posts_dir, filename)
        abs_path = os.path.abspath(file_path)
        
        if not abs_path.startswith(os.path.abspath(posts_dir)):
            return None
            
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return None
        
        if os.path.getsize(abs_path) > 5 * 1024 * 1024:
            return None
        
        if not os.access(abs_path, os.R_OK):
            return None
            
        metadata, content = parse_text_file(abs_path)
        
        return TextPost(filename, content, metadata)
        
    except Exception as e:
        current_app.logger.error(f"텍스트 포스트 로드 오류 (파일: {filename}): {str(e)}")
        return None


def get_tags_count(posts_dir=None):
    """모든 텍스트 파일의 태그 카운트 반환 - 캐싱 적용"""
    global _tags_cache, _cache_timestamp
    
    # 캐시 확인
    cache_timeout = current_app.config.get('CACHE_TIMEOUT', 300)
    if _tags_cache and _cache_timestamp and (time.time() - _cache_timestamp < cache_timeout):
        return _tags_cache.copy()
    
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
    
    _tags_cache = tags_count
    
    return tags_count.copy()


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
        current_app.logger.error(f"이전/다음 포스트 조회 오류: {str(e)}")
        return None, None


def clear_cache():
    """캐시 초기화 함수"""
    global _posts_cache, _tags_cache, _cache_timestamp
    _posts_cache = None
    _tags_cache = None
    _cache_timestamp = None


def render_content(content, base_url_images='/posts/images', base_url_videos='/posts/videos', base_url_audios='/posts/audios'):
    """특수 태그를 HTML로 변환 후 마크다운 처리 및 URL 자동 링크 변환"""
    if not isinstance(content, str):
        return ""
    
    # URL 검증
    if not isinstance(base_url_images, str) or not base_url_images.startswith('/'):
        base_url_images = '/posts/images'
    if not isinstance(base_url_videos, str) or not base_url_videos.startswith('/'):
        base_url_videos = '/posts/videos'
    if not isinstance(base_url_audios, str) or not base_url_audios.startswith('/'):
        base_url_audios = '/posts/audios'
    
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
    
    # 1단계: 특수 태그 변환
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
    
    # 2단계: 마크다운 처리
    if MARKDOWN_ENABLED:
        try:
            extensions = ['extra', 'nl2br', 'sane_lists']
            extension_configs = {
                'nl2br': {},
                'extra': {},
                'sane_lists': {}
            }
            
            md_content = markdown.markdown(content, extensions=extensions, extension_configs=extension_configs)
            
            # 허용된 HTML 태그 정의
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
            current_app.logger.error(f"마크다운 처리 오류: {str(e)}")
            cleaned_content = _process_content_legacy(content)
    else:
        cleaned_content = _process_content_legacy(content)
    
    # 3단계: URL 자동 링크 변환
    cleaned_content = _auto_linkify_urls(cleaned_content)
    
    return Markup(cleaned_content)


def _auto_linkify_urls(text):
    """텍스트 내의 일반 URL을 자동으로 클릭 가능한 링크로 변환"""
    if not isinstance(text, str):
        return text
    
    # URL 패턴
    url_pattern = re.compile(
        r'(?<!href=")(?<!src=")'
        r'(https?://[^\s<>"\']+)',
        re.IGNORECASE
    )
    
    def url_replacer(match):
        url = match.group(1)
        # URL 끝의 문장부호 제거
        url = url.rstrip('.,;:!?')
        
        # 보안을 위한 URL 이스케이핑
        safe_url = escape(url)
        
        # 표시할 텍스트 생성
        if len(url) > 60:
            display_text = url[:57] + "..."
        else:
            display_text = url
        
        return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer" class="auto-link">{escape(display_text)}</a>'
    
    return url_pattern.sub(url_replacer, text)


# ===== 헬퍼 함수들 =====

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
    """안전한 이미지 태그 생성"""
    if not isinstance(src, str) or not src or '..' in src or '/' in src:
        return '<div class="error-embed">잘못된 이미지 경로</div>'
    
    # 위험한 문자 체크
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
    """비디오 임베드 HTML 생성"""
    if not isinstance(video_filename, str) or not video_filename or '..' in video_filename or '/' in video_filename:
        return '<div class="error-embed">잘못된 비디오 파일명</div>'
    
    # 위험한 문자 체크
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
    """오디오 임베드 HTML 생성"""
    if not isinstance(audio_filename, str) or not audio_filename or '..' in audio_filename or '/' in audio_filename:
        return '<div class="error-embed">잘못된 오디오 파일명</div>'
    
    # 위험한 문자 체크
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
    """기존 방식으로 텍스트 처리 (마크다운 라이브러리 없을 때 사용)"""
    lines = content.split('\n')
    processed_lines = []
    in_code_block = False
    current_paragraph = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                paragraph_text = _auto_linkify_urls(paragraph_text)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            processed_lines.append('<br>')
            continue
        
        if line.startswith('```'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
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
        paragraph_text = _auto_linkify_urls(paragraph_text)
        processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
    
    return '\n'.join(processed_lines)