# app/services/text_service.py
import os
import re
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
        self.series = None  # 시리즈 정보 추가
        self.series_part = None  # 시리즈 순서 추가
        self.changelog = []  # 수정 이력 추가
        
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
            
            # 시리즈 정보 파싱
            series_str = metadata.get('series')
            if series_str:
                self.series = series_str
            
            series_part_str = metadata.get('series-part')
            if series_part_str:
                try:
                    self.series_part = int(series_part_str)
                except ValueError:
                    self.series_part = 1
            
            # 수정 이력 파싱
            changelog_str = metadata.get('changelog')
            if changelog_str:
                self.changelog = [item.strip() for item in changelog_str.split(',')]
    
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
        text = re.sub(r'\[youtube:[^\]]+\]', '', text)  # 유튜브 태그 제거
        text = re.sub(r'\[twitch:[^\]]+\]', '', text)   # 트위치 태그 제거
        text = re.sub(r'\[twitter:[^\]]+\]', '', text)  # 트위터 태그 제거
        text = re.sub(r'\[instagram:[^\]]+\]', '', text) # 인스타그램 태그 제거
        text = re.sub(r'\[facebook:[^\]]+\]', '', text) # 페이스북 태그 제거
        
        # 새로 추가된 태그들 제거
        text = re.sub(r'\[highlight\].*?\[/highlight\]', '', text)
        text = re.sub(r'\[quote.*?\].*?\[/quote\]', '', text)
        text = re.sub(r'\[pullquote.*?\].*?\[/pullquote\]', '', text)
        text = re.sub(r'\[gallery\].*?\[/gallery\]', '', text)
        text = re.sub(r'\[related\].*?\[/related\]', '', text)
        text = re.sub(r'\[changelog\].*?\[/changelog\]', '', text)
        
        text = re.sub(r'#+ ', '', text)  # 마크다운 헤더 태그 제거
        text = re.sub(r'\*\*|\*|__', '', text)  # 강조 태그 제거
        
        # 길이 제한
        if len(text) > length:
            return text[:length] + "..."
        return text
    
    def get_word_count(self):
        """글자 수 반환"""
        # 특수 태그 제거 (위와 동일한 방식)
        text = re.sub(r'\[img:[^\]]+\]', '', self.content)
        text = re.sub(r'\[file:[^\]]+\]', '', text)
        text = re.sub(r'\[youtube:[^\]]+\]', '', text)
        text = re.sub(r'\[twitch:[^\]]+\]', '', text)
        text = re.sub(r'\[twitter:[^\]]+\]', '', text)
        text = re.sub(r'\[instagram:[^\]]+\]', '', text)
        text = re.sub(r'\[facebook:[^\]]+\]', '', text)
        
        # 새로 추가된 태그들 제거
        text = re.sub(r'\[highlight\].*?\[/highlight\]', '', text)
        text = re.sub(r'\[quote.*?\].*?\[/quote\]', '', text)
        text = re.sub(r'\[pullquote.*?\].*?\[/pullquote\]', '', text)
        text = re.sub(r'\[gallery\].*?\[/gallery\]', '', text)
        text = re.sub(r'\[related\].*?\[/related\]', '', text)
        text = re.sub(r'\[changelog\].*?\[/changelog\]', '', text)
        
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
            meta_match = re.match(r'\[(\w+[\-\w]*?):\s*(.*?)\]', line)
            if meta_match:
                key, value = meta_match.groups()
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
        print(f"파일 파싱 오류: {str(e)}")
        return {}, ""


def render_content(content, base_url_images, base_url_files):
    """특수 태그를 HTML로 변환"""
    # 소셜 미디어 임베드를 먼저 처리 (마크다운 변환 전)
    # 이렇게 하면 임베드 HTML이 마크다운에 의해 이스케이프되지 않음
    
    # YouTube 임베드 변환
    content = re.sub(
        r'\[youtube:([^\]]+)\]',
        lambda m: _create_youtube_embed(m.group(1)),
        content
    )
    
    # Twitch 임베드 변환
    content = re.sub(
        r'\[twitch:([^\]]+)\]',
        lambda m: _create_twitch_embed(m.group(1)),
        content
    )
    
    # Twitter 임베드 변환
    content = re.sub(
        r'\[twitter:([^\]]+)\]',
        lambda m: _create_twitter_embed(m.group(1)),
        content
    )
    
    # Instagram 임베드 변환
    content = re.sub(
        r'\[instagram:([^\]]+)\]',
        lambda m: _create_instagram_embed(m.group(1)),
        content
    )
    
    # Facebook 임베드 변환
    content = re.sub(
        r'\[facebook:([^\]]+)\]',
        lambda m: _create_facebook_embed(m.group(1)),
        content
    )
    
    # 새로운 기능 1: 강조 내용 처리
    content = re.sub(
        r'\[highlight\](.*?)\[/highlight\]',
        lambda m: _create_highlight_box(m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    # 새로운 기능 4: 인용문 처리
    content = re.sub(
        r'\[quote(?:\s+author="([^"]*)")?\](.*?)\[/quote\]',
        lambda m: _create_quote_box(m.group(2), m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    # 새로운 기능 5: 큰 인용구 처리
    content = re.sub(
        r'\[pullquote(?:\s+align="([^"]*)")?\](.*?)\[/pullquote\]',
        lambda m: _create_pullquote(m.group(2), m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    # 새로운 기능 7: 확장된 이미지 속성
    content = re.sub(
        r'\[img:([^\]|]+)(?:\|([^\]|]*))?(?:\|([^\]]+))?\]',
        lambda m: _create_image_with_attributes(m.group(1), m.group(2), m.group(3), base_url_images),
        content
    )
    
    # 새로운 기능 6: 갤러리 처리
    content = re.sub(
        r'\[gallery\](.*?)\[/gallery\]',
        lambda m: _create_gallery(m.group(1), base_url_images),
        content,
        flags=re.DOTALL
    )
    
    # 새로운 기능 12: 관련 글 링크
    content = re.sub(
        r'\[related\](.*?)\[/related\]',
        lambda m: _create_related_posts(m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    # 새로운 기능 13: 시리즈 표시
    content = re.sub(
        r'\[series(?:\s+name="([^"]*)")?(?:\s+part="([^"]*)")?\]',
        lambda m: _create_series_box(m.group(1), m.group(2)),
        content
    )
    
    # 새로운 기능 14: 수정 이력
    content = re.sub(
        r'\[changelog\](.*?)\[/changelog\]',
        lambda m: _create_changelog(m.group(1)),
        content,
        flags=re.DOTALL
    )
    
    # 기존 기능: 이미지 태그 변환 (확장 속성이 없는 경우)
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
    
    # 텍스트 파일 간격 조정을 위한 전처리
    # 1. 빈 줄(연속된 두 줄바꿈)은 문단 구분으로 보존
    content = re.sub(r'\n\n+', '\n\n', content)  # 연속된 여러 줄바꿈을 두 개로 통일
    
    # 2. 마크다운 헤더 강화 - #으로 시작하는 라인이 정확히 헤더로 인식되도록 처리
    lines = content.split('\n')
    for i in range(len(lines)):
        line = lines[i].strip()
        
        if line and line[0] == '#':
            # 헤더 수준 확인 (# 개수 세기)
            header_level = 0
            for char in line:
                if char == '#':
                    header_level += 1
                else:
                    break
            
            # #과 텍스트 사이에 공백이 있는지 확인
            if len(line) > header_level and line[header_level] != ' ':
                # 공백이 없으면 추가
                lines[i] = line[:header_level] + ' ' + line[header_level:]
            
    content = '\n'.join(lines)
    
    # 3. 각 줄을 개별적으로 마크다운 처리하기 위한 준비
    lines = content.split('\n')
    processed_lines = []
    
    # 각 줄마다 독립적인 마크다운 처리
    for line in lines:
        line = line.strip()
        if not line:  # 빈 줄 처리
            processed_lines.append('<br>')
            continue
            
        # 헤더 처리 (#으로 시작하는 줄)
        if line.startswith('#'):
            # 헤더 수준 확인
            header_level = 0
            for char in line:
                if char == '#':
                    header_level += 1
                else:
                    break
                    
            if header_level > 0 and len(line) > header_level and line[header_level] == ' ':
                header_text = line[header_level+1:].strip()
                processed_lines.append(f'<h{header_level}>{header_text}</h{header_level}>')
                continue
        
        # 일반 텍스트 처리 (마크다운 변환 없이 일반 텍스트로 유지)
        processed_lines.append(f'<p class="compact-text">{line}</p>')
    
    # HTML로 조합
    html_content = '\n'.join(processed_lines)
    
    return html_content


def _create_highlight_box(content):
    """강조 내용 박스 생성"""
    return f'<div class="highlight-box">{content}</div>'


def _create_quote_box(content, author=None):
    """인용문 박스 생성"""
    author_html = f'<span class="blockquote-author">{author}</span>' if author else ''
    return f'<blockquote class="styled-quote">{content}{author_html}</blockquote>'


def _create_pullquote(content, align=None):
    """큰 인용구 생성"""
    align_class = f"align-{align}" if align in ["left", "right", "center"] else "align-center"
    return f'<div class="pullquote {align_class}">{content}</div>'


def _create_image_with_attributes(image_path, caption=None, attributes=None, base_url_images=None):
    """확장 속성을 가진 이미지 생성"""
    # 속성 파싱
    align = "center"
    size = "medium"
    width = ""
    height = ""
    
    if attributes:
        align_match = re.search(r'align="([^"]*)"', attributes)
        if align_match:
            align = align_match.group(1)
        
        size_match = re.search(r'size="([^"]*)"', attributes)
        if size_match:
            size = size_match.group(1)
        
        width_match = re.search(r'width="([^"]*)"', attributes)
        if width_match:
            width = f'width="{width_match.group(1)}"'
        
        height_match = re.search(r'height="([^"]*)"', attributes)
        if height_match:
            height = f'height="{height_match.group(1)}"'
    
    # 클래스 생성
    classes = f"post-image align-{align} size-{size}"
    
    # 캡션 처리
    caption_html = f'<figcaption>{caption}</figcaption>' if caption else ''
    
    return f'''
    <figure class="{classes}">
        <img src="{base_url_images}/{image_path}" alt="{caption if caption else image_path}" {width} {height} class="text-post-image">
        {caption_html}
    </figure>
    '''


def _create_gallery(content, base_url_images):
    """갤러리 생성"""
    # 쉼표로 구분된 이미지 목록 파싱
    images = [img.strip() for img in content.split(',')]
    
    # 갤러리 시작 태그
    gallery_html = '<div class="gallery">'
    
    # 각 이미지 추가
    for img in images:
        # 이미지와 캡션 분리
        parts = img.split('|')
        image_path = parts[0].strip()
        caption = parts[1].strip() if len(parts) > 1 else image_path
        
        gallery_html += f'''
        <div class="gallery-item">
            <img src="{base_url_images}/{image_path}" alt="{caption}" class="gallery-image">
            <div class="gallery-caption">{caption}</div>
        </div>
        '''
    
    # 갤러리 닫는 태그
    gallery_html += '</div>'
    
    return gallery_html


def _create_related_posts(content):
    """관련 글 링크 생성"""
    # 줄별로 분리
    lines = content.split('\n')
    related_items = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('-') or line.startswith('*'):
            item = line[1:].strip()
            if '|' in item:
                # 제목과 URL이 분리되어 있는 경우
                title, url = [part.strip() for part in item.split('|', 1)]
                related_items.append((title, url))
            else:
                # 제목만 있는 경우
                related_items.append((item, "#"))
    
    # HTML 생성
    related_html = '<div class="related-posts-box"><h4>관련 글</h4><ul class="related-posts-list">'
    
    for title, url in related_items:
        related_html += f'<li><a href="{url}">{title}</a></li>'
    
    related_html += '</ul></div>'
    
    return related_html


def _create_series_box(series_name, part=None):
    """시리즈 정보 박스 생성"""
    part_text = f"파트 {part}" if part else ""
    series_title = f"{series_name} {part_text}".strip()
    
    return f'''
    <div class="series-box">
        <div class="series-title">{series_title}</div>
        <div class="series-info">이 글은 {series_name} 시리즈의 일부입니다.</div>
    </div>
    '''


def _create_changelog(content):
    """수정 이력 생성"""
    lines = content.split('\n')
    changelog_items = []
    
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('-') or line.startswith('*'):
                item = line[1:].strip()
                changelog_items.append(item)
            else:
                changelog_items.append(line)
    
    changelog_html = '<div class="changelog-box"><h4>수정 이력</h4><ul class="changelog-list">'
    
    for item in changelog_items:
        changelog_html += f'<li>{item}</li>'
    
    changelog_html += '</ul></div>'
    
    return changelog_html


def _create_youtube_embed(youtube_id_or_url):
    """유튜브 임베드 HTML 생성"""
    # URL에서 동영상 ID 추출
    if 'youtube.com' in youtube_id_or_url or 'youtu.be' in youtube_id_or_url:
        if 'youtube.com/watch' in youtube_id_or_url:
            # https://www.youtube.com/watch?v=VIDEO_ID 형식
            match = re.search(r'v=([^&]+)', youtube_id_or_url)
            if match:
                youtube_id = match.group(1)
            else:
                return f'<div class="error-embed">잘못된 YouTube URL: {youtube_id_or_url}</div>'
        elif 'youtu.be/' in youtube_id_or_url:
            # https://youtu.be/VIDEO_ID 형식
            youtube_id = youtube_id_or_url.split('/')[-1]
        else:
            return f'<div class="error-embed">지원되지 않는 YouTube URL 형식: {youtube_id_or_url}</div>'
    else:
        # 이미 ID만 제공된 경우
        youtube_id = youtube_id_or_url
    
    # 임베드 HTML 생성 (사진과 같은 크기로 설정, 16:9 비율 유지)
    embed_html = f'''
<div class="social-embed youtube-embed">
    <iframe width="880" height="495" src="https://www.youtube.com/embed/{youtube_id}" 
    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen></iframe>
</div>
'''
    return embed_html


def _create_twitch_embed(twitch_id_or_url):
    """트위치 임베드 HTML 생성"""
    # URL 또는 채널명/클립ID 처리
    if 'twitch.tv' in twitch_id_or_url:
        # 트위치 URL 처리
        if '/clip/' in twitch_id_or_url:
            # 클립 URL
            clip_id = twitch_id_or_url.split('/')[-1]
            embed_html = f'''
<div class="social-embed twitch-embed">
    <iframe width="880" height="495" src="https://clips.twitch.tv/embed?clip={clip_id}" 
    frameborder="0" allowfullscreen="true" scrolling="no"></iframe>
</div>
'''
        else:
            # 채널 URL
            channel_name = twitch_id_or_url.split('/')[-1]
            embed_html = f'''
<div class="social-embed twitch-embed">
    <iframe width="880" height="495" src="https://player.twitch.tv/?channel={channel_name}&parent=localhost" 
    frameborder="0" allowfullscreen="true" scrolling="no"></iframe>
</div>
'''
    else:
        # 채널명이나 클립ID만 제공된 경우
        # 클립 ID인지 채널명인지 구분하기 어려우므로 기본적으로 채널로 간주
        embed_html = f'''
<div class="social-embed twitch-embed">
    <iframe width="880" height="495" src="https://player.twitch.tv/?channel={twitch_id_or_url}&parent=localhost" 
    frameborder="0" allowfullscreen="true" scrolling="no"></iframe>
</div>
'''
    return embed_html


def _create_twitter_embed(tweet_id_or_url):
    """트위터 임베드 HTML 생성"""
    # URL에서 트윗 ID 추출
    if 'twitter.com' in tweet_id_or_url or 'x.com' in tweet_id_or_url:
        # https://twitter.com/username/status/TWEET_ID 형식
        tweet_id = tweet_id_or_url.split('/')[-1]
    else:
        # 이미 ID만 제공된 경우
        tweet_id = tweet_id_or_url
    
    # 임베드 HTML 생성
    embed_html = f'''
<div class="social-embed twitter-embed">
    <blockquote class="twitter-tweet" data-width="880">
        <a href="https://twitter.com/x/status/{tweet_id}"></a>
    </blockquote>
</div>
'''
    return embed_html


def _create_instagram_embed(post_id_or_url):
    """인스타그램 임베드 HTML 생성"""
    # URL에서 포스트 ID 추출
    if 'instagram.com' in post_id_or_url:
        # https://www.instagram.com/p/POST_ID/ 형식
        if '/p/' in post_id_or_url:
            post_id = post_id_or_url.split('/p/')[-1].strip('/')
        else:
            return f'<div class="error-embed">지원되지 않는 Instagram URL 형식: {post_id_or_url}</div>'
    else:
        # 이미 ID만 제공된 경우
        post_id = post_id_or_url
    
    # 임베드 HTML 생성 (880px 너비)
    embed_html = f'''
<div class="social-embed instagram-embed" style="width:880px; max-width:100%;">
    <blockquote class="instagram-media" data-width="880"
    data-instgrm-permalink="https://www.instagram.com/p/{post_id}/"
    style="width:880px; max-width:100%;">
        <a href="https://www.instagram.com/p/{post_id}/"></a>
    </blockquote>
</div>
'''
    return embed_html


def _create_facebook_embed(post_id_or_url):
    """페이스북 임베드 HTML 생성"""
    # 임베드 HTML 생성
    embed_html = f'''
<div class="social-embed facebook-embed" style="width:880px; max-width:100%;">
    <div class="fb-post" data-href="{post_id_or_url}" data-width="880"></div>
</div>
'''
    return embed_html


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


def get_series_posts(text_dir, series_name):
    """시리즈에 속한 모든 포스트 검색"""
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

# 수정된 함수: 이전/다음 포스트 가져오기
def get_adjacent_posts(text_dir, current_post):
    """현재 포스트의 이전 및 다음 포스트 반환"""
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