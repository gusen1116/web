# app/services/text_service.py
import os
import re
# shutil 모듈 제거 - 미사용
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
        text = re.sub(r'\[youtube:[^\]]+\]', '', text)  # 유튜브 태그 제거
        text = re.sub(r'\[twitch:[^\]]+\]', '', text)   # 트위치 태그 제거
        text = re.sub(r'\[twitter:[^\]]+\]', '', text)  # 트위터 태그 제거
        text = re.sub(r'\[instagram:[^\]]+\]', '', text) # 인스타그램 태그 제거
        text = re.sub(r'\[facebook:[^\]]+\]', '', text) # 페이스북 태그 제거
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
        text = re.sub(r'\[youtube:[^\]]+\]', '', text)
        text = re.sub(r'\[twitch:[^\]]+\]', '', text)
        text = re.sub(r'\[twitter:[^\]]+\]', '', text)
        text = re.sub(r'\[instagram:[^\]]+\]', '', text)
        text = re.sub(r'\[facebook:[^\]]+\]', '', text)
        
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
    
    # 마크다운 변환을 위해 마크다운 라이브러리 사용
    # nl2br 확장을 추가하여 줄 바꿈을 <br> 태그로 변환
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'nl2br'])
    
    # 마크다운 변환
    html_content = md.convert(content)
    
    return html_content


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