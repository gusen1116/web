# app/services/text_service.py (보안 강화 버전)
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from flask import url_for, current_app
from markupsafe import escape, Markup
from werkzeug.utils import secure_filename

# 마크다운 처리를 위한 임포트 (선택적)
try:
    import markdown
    import bleach
    MARKDOWN_ENABLED = True
except ImportError:
    MARKDOWN_ENABLED = False

# HTML 파싱을 위한 임포트
try:
    from html.parser import HTMLParser
    HTML_PARSER_ENABLED = True
except ImportError:
    HTML_PARSER_ENABLED = False

# 상수 정의 - 보안 및 성능 최적화
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (읽기용)
CACHE_VERSION = "v2.0"  # 캐시 버전 관리


class URLLinkifyParser(HTMLParser):
    """HTML 내의 텍스트 노드만 추출하여 URL 링크 변환"""
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_tag = None
        self.tag_stack = []
    
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        self.in_tag = tag
        
        # 태그를 그대로 결과에 추가
        attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs])
        if attrs_str:
            self.result.append(f'<{tag} {attrs_str}>')
        else:
            self.result.append(f'<{tag}>')
    
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        self.in_tag = self.tag_stack[-1] if self.tag_stack else None
        self.result.append(f'</{tag}>')
    
    def handle_data(self, data):
        # a, script, style 태그 내부는 변환하지 않음
        if self.in_tag in ['a', 'script', 'style', 'code', 'pre']:
            self.result.append(data)
        else:
            # 텍스트 노드에서만 URL 변환
            self.result.append(_linkify_text_urls(data))


@dataclass
class TextPost:
    """텍스트 파일 기반 포스트 클래스 - 타입 안전성 강화"""
    
    filename: str
    content: str
    id: str = field(init=False)
    
    # 메타데이터 기본값
    title: str = ""
    date: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    author: str = "구센"
    description: str = ""
    subtitle: str = ""
    slug: Optional[str] = None
    series: Optional[str] = None
    series_part: Optional[int] = None
    changelog: List[str] = field(default_factory=list)
    
    # 캐시된 값들
    _hash: Optional[str] = field(default=None, init=False)
    _word_count: Optional[int] = field(default=None, init=False)
    _preview: Optional[str] = field(default=None, init=False)
    
    def __post_init__(self):
        """초기화 후 처리"""
        if not self._validate_filename(self.filename):
            raise ValueError(f"잘못된 파일명: {self.filename}")
        
        self.id = Path(self.filename).stem
        self.title = self.title or self.filename
        
        # 슬러그 기본값 설정
        if not self.slug:
            self.slug = self._generate_safe_slug(self.id)
    
    @staticmethod
    def _validate_filename(filename: str) -> bool:
        """파일명 보안 검증 강화"""
        if not isinstance(filename, str) or not filename:
            return False
        
        # secure_filename으로 검증
        secure_name = secure_filename(filename)
        if secure_name != filename:
            return False
        
        # 위험한 패턴 검사
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # 파일명 길이 검사
        if len(filename) > 255:
            return False
        
        # 허용된 확장자만 허용
        allowed_extensions = current_app.config.get('ALLOWED_TEXT_EXTENSIONS', {'txt', 'md'})
        if not any(filename.lower().endswith(f'.{ext}') for ext in allowed_extensions):
            return False
        
        return True
    
    @staticmethod
    def _generate_safe_slug(text: str) -> str:
        """안전한 슬러그 생성"""
        # 특수문자 제거 및 하이픈으로 치환
        slug = re.sub(r'[^\w가-힣\s-]', '', text.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = slug.strip('-')
        
        # 길이 제한
        return slug[:100] if slug else text[:100]
    
    def update_from_metadata(self, metadata: Dict[str, str]) -> None:
        """메타데이터로부터 안전하게 업데이트"""
        # 제목 처리
        if 'title' in metadata:
            title = str(metadata['title'])[:current_app.config.get('MAX_TITLE_LENGTH', 200)]
            self.title = escape(title)
        
        # 설명 처리
        if 'description' in metadata:
            desc = str(metadata['description'])[:500]
            self.description = escape(desc)
        
        # 부제목 처리
        if 'subtitle' in metadata:
            subtitle = str(metadata['subtitle'])[:200]
            self.subtitle = escape(subtitle)
        
        # 작성자 처리
        if 'author' in metadata:
            author = str(metadata['author'])[:50]
            self.author = escape(author)
        
        # 슬러그 처리 - 보안 강화
        if 'slug' in metadata:
            slug = str(metadata['slug'])[:100]
            if re.match(r'^[a-zA-Z0-9_\-가-힣]+$', slug):
                self.slug = slug
        
        # 날짜 파싱
        if 'date' in metadata:
            self._parse_date(metadata['date'])
        
        # 태그 파싱
        if 'tags' in metadata:
            self._parse_tags(metadata['tags'])
        
        # 시리즈 정보 처리
        self._parse_series_info(metadata)
        
        # 수정 이력 처리
        if 'changelog' in metadata:
            self._parse_changelog(metadata['changelog'])
    
    def _parse_date(self, date_str: str) -> None:
        """날짜 파싱 - 다양한 형식 지원"""
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M'
        ]
        
        for fmt in date_formats:
            try:
                self.date = datetime.strptime(str(date_str).strip(), fmt)
                self.created_at = self.date
                return
            except ValueError:
                continue
        
        current_app.logger.warning(f"날짜 파싱 실패: {date_str}, 기본값 사용")
    
    def _parse_tags(self, tags_str: str) -> None:
        """태그 파싱 - 보안 강화"""
        max_tags = current_app.config.get('MAX_TAGS_PER_POST', 15)
        max_tag_length = current_app.config.get('MAX_TAG_LENGTH', 50)
        
        self.tags = []
        raw_tags = str(tags_str).split(',')
        
        for tag in raw_tags[:max_tags]:
            tag = tag.strip()
            if not tag or len(tag) > max_tag_length:
                continue
            
            # 태그 문자 검증
            if re.match(r'^[가-힣a-zA-Z0-9\s\-_]+$', tag):
                self.tags.append(escape(tag))
    
    def _parse_series_info(self, metadata: Dict[str, str]) -> None:
        """시리즈 정보 파싱"""
        if 'series' in metadata:
            series = str(metadata['series'])[:100]
            if re.match(r'^[가-힣a-zA-Z0-9\s\-_]+$', series):
                self.series = escape(series)
        
        if 'series-part' in metadata:
            try:
                part = int(metadata['series-part'])
                if 0 < part < 1000:
                    self.series_part = part
            except (ValueError, TypeError):
                current_app.logger.warning(f"시리즈 파트 파싱 실패: {metadata['series-part']}")
    
    def _parse_changelog(self, changelog_str: str) -> None:
        """수정 이력 파싱"""
        self.changelog = []
        for item in str(changelog_str).split(',')[:10]:
            item = item.strip()[:200]
            if item:
                self.changelog.append(escape(item))
    
    def get_url(self) -> str:
        """포스트 URL 반환"""
        return url_for('posts.view_by_slug', slug=self.slug or self.id)
    
    def get_preview(self, length: int = 200) -> str:
        """본문 미리보기 생성 (텍스트 전용) - 캐싱 적용"""
        length = max(50, min(length, current_app.config.get('MAX_PREVIEW_LENGTH', 300)))
        
        # 캐시된 미리보기가 있고 길이가 적절하면 사용
        if self._preview and len(self._preview) >= length:
            return self._preview[:length] + ("..." if len(self._preview) > length else "")
        
        # 미리보기 생성
        preview = self._generate_preview_text(length)
        self._preview = preview
        return preview
    
    def _generate_preview_text(self, length: int) -> str:
        """미리보기 텍스트 생성"""
        # 특수 태그 제거 패턴들
        patterns_to_remove = [
            r'\[img:[^\]]+\]',
            r'\[video:[^\]]+\]',
            r'\[audio:[^\]]+\]',
            r'\[youtube:[^\]]+\]',
            r'\[highlight\].*?\[/highlight\]',
            r'\[quote.*?\].*?\[/quote\]',
            r'\[.*?\]',
            r'#+\s+',
            r'\*\*|\*|__|_',
            r'!\[.*?\]\(.*?\)',
            r'\[.*?\]\(.*?\)',
        ]
        
        text = self.content
        for pattern in patterns_to_remove:
            text = re.sub(pattern, ' ', text, flags=re.DOTALL | re.MULTILINE)
        
        # 연속된 공백 및 줄바꿈 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 길이 제한 및 단어 경계에서 자르기
        if len(text) <= length:
            return escape(text)
        
        preview_text = text[:length]
        last_space = preview_text.rfind(' ')
        if last_space > length * 0.8:
            preview_text = preview_text[:last_space]
        
        return escape(preview_text) + "..."

    def get_rich_preview(self, text_length: int = 150) -> Dict[str, Optional[str]]:
        """본문 미리보기 텍스트와 첫 번째 이미지 파일명 및 alt 텍스트를 반환"""
        # 1. 텍스트 미리보기 생성
        text_preview_content = self._generate_preview_text(text_length)

        # 2. 첫 번째 이미지 파일명 및 alt 텍스트 찾기
        first_image_filename: Optional[str] = None
        first_image_alt: str = ""

        # 이미지 태그 패턴
        img_match = re.search(r'\[img:([^\]|]+)(?:\|([^\]|]*))?(?:\|[^\]]*)?\]', self.content)

        if img_match:
            filename_from_tag = img_match.group(1).strip()
            alt_text_from_tag = img_match.group(2).strip() if img_match.group(2) and img_match.group(2).strip() else filename_from_tag
            
            # secure_filename으로 파일명 검증
            secure_name = secure_filename(filename_from_tag)
            if secure_name == filename_from_tag:
                allowed_img_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
                if any(filename_from_tag.lower().endswith(f".{ext}") for ext in allowed_img_extensions):
                    first_image_filename = filename_from_tag
                    first_image_alt = alt_text_from_tag
        
        return {
            "text": text_preview_content,
            "image_filename": first_image_filename,
            "image_alt": escape(first_image_alt)
        }

    def get_word_count(self) -> int:
        """단어 수 반환 - 캐싱 적용"""
        if self._word_count is not None:
            return self._word_count
        
        # 특수 태그 제거
        text = re.sub(r'\[.*?\]', '', self.content, flags=re.DOTALL)
        text = re.sub(r'[#*_`~]', '', text)
        
        # 단어/문자 카운트 (한글 고려)
        words = re.findall(r'\w+', text)
        korean_chars = len(re.findall(r'[가-힣]', text))
        
        self._word_count = len(words) + korean_chars // 2
        return self._word_count
    
    def get_file_hash(self) -> str:
        """파일 해시 반환 - 캐싱 적용"""
        if not self._hash:
            content = f"{self.filename}:{self.content}:{CACHE_VERSION}"
            self._hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return self._hash


def parse_text_file(file_path: Union[str, Path]) -> Tuple[Dict[str, str], str]:
    """텍스트 파일 파싱 - 보안 및 성능 강화"""
    file_path = Path(file_path)
    
    # 경로 보안 검증
    if not _validate_file_path(file_path):
        raise ValueError(f"잘못된 파일 경로: {file_path}")
    
    # 파일 존재 및 크기 검사
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없음: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"디렉토리는 파일이 아님: {file_path}")
    
    file_size = file_path.stat().st_size
    max_size = current_app.config.get('MAX_FILE_READ_SIZE', MAX_FILE_SIZE)
    if file_size > max_size:
        raise ValueError(f"파일 크기 초과: {file_size} > {max_size}")
    
    try:
        # 파일 읽기
        content = _read_file_safe(file_path)
        
        # 메타데이터 추출
        metadata, body = _extract_metadata_and_body(content)
        
        return metadata, body
        
    except UnicodeDecodeError as e:
        current_app.logger.error(f"파일 인코딩 오류 {file_path}: {e}")
        raise ValueError(f"파일 인코딩 오류: {e}")
    except Exception as e:
        current_app.logger.error(f"파일 파싱 오류 {file_path}: {e}")
        raise


def _validate_file_path(file_path: Path) -> bool:
    """파일 경로 보안 검증"""
    try:
        # 절대 경로 변환
        abs_path = file_path.resolve()
        
        # 허용된 디렉토리 내부인지 확인
        posts_dir = Path(current_app.config.get('POSTS_DIR')).resolve()
        if not str(abs_path).startswith(str(posts_dir)):
            current_app.logger.warning(f"경로 접근 위반 시도: {file_path}")
            return False
        
        # 위험한 경로 패턴 검사
        dangerous_parts = {'..', '.', '~', '$'}
        if any(part in dangerous_parts for part in abs_path.parts):
            return False
        
        return True
        
    except (OSError, ValueError):
        return False


def _read_file_safe(file_path: Path) -> str:
    """파일 안전 읽기"""
    encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    
    # 모든 인코딩 실패 시
    with open(file_path, 'rb') as file:
        content = file.read()
        return content.decode('utf-8', errors='replace')


def _extract_metadata_and_body(content: str) -> Tuple[Dict[str, str], str]:
    """메타데이터와 본문 분리"""
    lines = content.split('\n')
    metadata = {}
    content_start = 0
    
    # 메타데이터 패턴
    meta_pattern = re.compile(r'^\[([a-zA-Z\-_]+):\s*(.+?)\]$')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        match = meta_pattern.match(line)
        if match:
            key, value = match.groups()
            # 키 길이 제한 및 검증
            if len(key) <= 50 and re.match(r'^[a-zA-Z\-_]+$', key):
                metadata[key.lower()] = value.strip()
            content_start = i + 1
        else:
            # 메타데이터가 아닌 줄을 만나면 중단
            break
    
    # 본문 추출
    body = '\n'.join(lines[content_start:]).strip()
    
    return metadata, body


def get_all_text_posts(posts_dir: Optional[str] = None, tag: Optional[str] = None) -> List[TextPost]:
    """모든 텍스트 파일 로드"""
    if posts_dir is None:
        posts_dir = current_app.config.get('POSTS_DIR')
    
    posts_dir = Path(posts_dir)
    posts = []
    
    if not posts_dir.exists() or not posts_dir.is_dir():
        current_app.logger.warning(f"포스트 디렉토리 없음: {posts_dir}")
        return posts
    
    try:
        # 허용된 확장자만 필터링
        allowed_extensions = current_app.config.get('ALLOWED_TEXT_EXTENSIONS', {'txt', 'md'})
        max_posts = current_app.config.get('MAX_POSTS_TOTAL', 2000)
        
        # 파일 목록 가져오기
        files = []
        for ext in allowed_extensions:
            pattern = f"*.{ext}"
            files.extend(posts_dir.glob(pattern))
        
        # 파일명으로 정렬 후 제한
        files = sorted(files, key=lambda f: f.name)[:max_posts]
        
        # 각 파일 처리
        for file_path in files:
            try:
                post = get_text_post(str(posts_dir), file_path.name)
                if post:
                    posts.append(post)
            except Exception as e:
                current_app.logger.error(f"포스트 로드 실패 {file_path.name}: {e}")
                continue
        
        # 날짜순 정렬 (최신순)
        posts.sort(key=lambda x: x.date, reverse=True)
        
        # 태그 필터링
        if tag and posts:
            posts = [p for p in posts if tag in p.tags]
            
    except Exception as e:
        current_app.logger.error(f"포스트 목록 로드 오류: {e}")
    
    return posts


def get_text_post(posts_dir: Union[str, Path], filename: str) -> Optional[TextPost]:
    """특정 텍스트 파일 로드"""
    try:
        # 파일명 사전 검증
        if not TextPost._validate_filename(filename):
            current_app.logger.warning(f"잘못된 파일명: {filename}")
            return None
        
        file_path = Path(posts_dir) / filename
        
        # 파일 파싱
        metadata, content = parse_text_file(file_path)
        
        # TextPost 객체 생성
        post = TextPost(filename=filename, content=content)
        
        # 메타데이터 적용
        if metadata:
            post.update_from_metadata(metadata)
        
        return post
        
    except Exception as e:
        current_app.logger.error(f"포스트 로드 오류 {filename}: {e}")
        return None


def get_tags_count(posts_dir: Optional[str] = None) -> Dict[str, int]:
    """모든 포스트의 태그 카운트 반환"""
    try:
        posts = get_all_text_posts(posts_dir)
        tags_count = {}
        
        for post in posts:
            for tag_item in post.tags:
                tags_count[tag_item] = tags_count.get(tag_item, 0) + 1
        
        return tags_count
        
    except Exception as e:
        current_app.logger.error(f"태그 카운트 오류: {e}")
        return {}


def get_series_posts(posts_dir: Union[str, Path], series_name: str) -> List[TextPost]:
    """시리즈에 속한 모든 포스트 검색"""
    if not series_name or not isinstance(series_name, str):
        return []
    
    try:
        all_posts = get_all_text_posts(str(posts_dir))
        series_posts = [post for post in all_posts if post.series == series_name]
        
        # 시리즈 파트 번호와 날짜로 정렬
        series_posts.sort(key=lambda x: (x.series_part or 9999, x.date))
        
        return series_posts
        
    except Exception as e:
        current_app.logger.error(f"시리즈 포스트 로드 오류 {series_name}: {e}")
        return []


def get_adjacent_posts(posts_dir: Union[str, Path], current_post: TextPost) -> Tuple[Optional[TextPost], Optional[TextPost]]:
    """현재 포스트의 이전/다음 포스트 반환"""
    if not isinstance(current_post, TextPost):
        return None, None
    
    try:
        all_posts = get_all_text_posts(str(posts_dir))
        
        # 현재 포스트 인덱스 찾기
        current_index = None
        for i, post in enumerate(all_posts):
            if post.id == current_post.id:
                current_index = i
                break
        
        if current_index is None:
            return None, None
        
        # 이전/다음 포스트
        prev_post = all_posts[current_index + 1] if current_index < len(all_posts) - 1 else None
        next_post = all_posts[current_index - 1] if current_index > 0 else None
        
        return prev_post, next_post
        
    except Exception as e:
        current_app.logger.error(f"인접 포스트 조회 오류: {e}")
        return None, None


# ===== 콘텐츠 렌더링 함수들 (보안 강화) =====

def render_content(content: str, 
                  base_url_images: str = '/posts/images', 
                  base_url_videos: str = '/posts/videos', 
                  base_url_audios: str = '/posts/audios') -> Markup:
    """특수 태그를 HTML로 변환 후 마크다운 처리"""
    if not isinstance(content, str) or not content.strip():
        return Markup("")
    
    # URL 보안 검증
    for url in [base_url_images, base_url_videos, base_url_audios]:
        if not isinstance(url, str) or not url.startswith('/'):
            current_app.logger.error(f"잘못된 URL 설정: {url}")
            return Markup("잘못된 URL 설정")
    
    try:
        # 특수 태그 처리
        processed_content = _process_special_tags(content, base_url_images, base_url_videos, base_url_audios)
        
        # 마크다운 처리
        if MARKDOWN_ENABLED:
            html_content = _process_markdown(processed_content)
        else:
            html_content = _process_content_fallback(processed_content)
        
        # HTML 정제
        clean_content = _sanitize_html_preserve_links(html_content)
        
        # URL 링크 변환
        final_content = _auto_linkify_urls_safe(clean_content)
        
        return Markup(final_content)
        
    except Exception as e:
        current_app.logger.error(f"콘텐츠 렌더링 오류: {e}")
        return Markup(f'<div class="content-error">일부 기능이 제한되었습니다.</div><div class="post-content">{escape(content)}</div>')


def _process_special_tags(content: str, base_url_images: str, base_url_videos: str, base_url_audios: str) -> str:
    """특수 태그 처리 - 보안 강화"""
    
    # 안전한 태그 변환 매핑
    replacements = [
        # YouTube 임베드
        (r'\[youtube:([^\]]+)\]', 
         lambda m: _create_youtube_embed(m.group(1))),
        
        # 이미지 - secure_filename 적용
        (r'\[img:([^\]|]+)(?:\|([^\]|]*))?(?:\|([^\]]*))?\]', 
         lambda m: _create_image_tag_secure(m.group(1), m.group(2), m.group(3), base_url_images)),
        
        # 비디오 - secure_filename 적용
        (r'\[video:([^\]|]+)(?:\|([^\]]*))?\]',
         lambda m: _create_video_tag_secure(m.group(1), m.group(2), base_url_videos)),
        
        # 오디오 - secure_filename 적용
        (r'\[audio:([^\]|]+)(?:\|([^\]]*))?\]',
         lambda m: _create_audio_tag_secure(m.group(1), m.group(2), base_url_audios)),
        
        # 하이라이트 박스
        (r'\[highlight\](.*?)\[/highlight\]', 
         lambda m: f'<div class="highlight-box">{escape(m.group(1))}</div>'),
        
        # 인용구
        (r'\[quote(?:\s+author="([^"]*)")?\](.*?)\[/quote\]', 
         lambda m: _create_quote_block(m.group(2), m.group(1))),
        
        # 코드 블록
        (r'\[code(?:\s+lang="([^"]*)")?\](.*?)\[/code\]',
         lambda m: _create_code_block(m.group(2), m.group(1))),
    ]
    
    # 특수 태그 변환 적용
    for pattern, handler in replacements:
        content = re.sub(pattern, handler, content, flags=re.DOTALL | re.MULTILINE)
    
    return content


def _create_youtube_embed(youtube_input: str) -> str:
    """유튜브 임베드 HTML 생성"""
    if not isinstance(youtube_input, str):
        return '<div class="error-embed">잘못된 YouTube URL</div>'
    
    youtube_id = _extract_youtube_id(youtube_input.strip())
    
    if not youtube_id:
        return '<div class="error-embed">잘못된 YouTube ID</div>'
    
    # YouTube ID 보안 검증
    if not re.match(r'^[a-zA-Z0-9_\-]{11}$', youtube_id):
        return '<div class="error-embed">잘못된 YouTube ID 형식</div>'
    
    return f'''
<div class="social-embed youtube-embed">
    <iframe src="https://www.youtube.com/embed/{escape(youtube_id)}" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen
            sandbox="allow-scripts allow-same-origin allow-presentation"
            loading="lazy"
            title="YouTube video"></iframe>
</div>
'''


def _extract_youtube_id(url_or_id: str) -> Optional[str]:
    """YouTube URL에서 ID 추출"""
    # 이미 ID인 경우
    if re.match(r'^[a-zA-Z0-9_\-]{11}$', url_or_id):
        return url_or_id
    
    # URL에서 ID 추출
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_\-]{11})',
        r'youtu\.be/([a-zA-Z0-9_\-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_\-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_\-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def _create_image_tag_secure(src: str, alt: Optional[str], options_str: Optional[str], base_url: str) -> str:
    """안전한 이미지 태그 생성 - secure_filename 적용"""
    if not isinstance(src, str) or not src.strip():
        return '<div class="error-embed">이미지 경로가 없습니다</div>'
    
    src = src.strip()
    
    # secure_filename으로 파일명 정제
    secure_src = secure_filename(src)
    if not secure_src:
        return '<div class="error-embed">잘못된 이미지 파일명</div>'
    
    # 파일 확장자 검증
    allowed_img_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    if not any(secure_src.lower().endswith(f".{ext}") for ext in allowed_img_extensions):
        return '<div class="error-embed">지원하지 않는 이미지 형식</div>'
    
    safe_src = escape(secure_src)
    safe_alt = escape(alt.strip()) if alt and alt.strip() else escape(Path(secure_src).stem)
    safe_base_url = escape(base_url.rstrip('/'))

    # 옵션 파싱
    style_attribute = "width: auto; max-width: 100%;"
    if options_str:
        options = {}
        parts = options_str.split('|')
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                if key in ['width', 'scale']:
                    options[key] = value
                    break

        if 'width' in options:
            try:
                width_val = int(options['width'])
                if 10 <= width_val <= 2000:
                    style_attribute = f"width: {width_val}px; max-width: 100%; height: auto;"
            except ValueError:
                pass
        elif 'scale' in options:
            try:
                scale_val = int(options['scale'])
                if 10 <= scale_val <= 100:
                    style_attribute = f"width: {scale_val}%; max-width: 100%; height: auto;"
            except ValueError:
                pass
    
    # loading="lazy"와 decoding="async" 속성 추가
    return f'''
<figure class="post-image">
    <img src="{safe_base_url}/{safe_src}" 
         alt="{safe_alt}" 
         class="text-post-image"
         loading="lazy"
         decoding="async"
         style="{style_attribute}">
    {f'<figcaption>{safe_alt}</figcaption>' if alt and alt.strip() else ''}
</figure>
'''


def _create_video_tag_secure(src: str, title: Optional[str], base_url: str) -> str:
    """안전한 비디오 태그 생성 - secure_filename 적용"""
    if not isinstance(src, str) or not src.strip():
        return '<div class="error-embed">비디오 경로가 없습니다</div>'
    
    src = src.strip()
    
    # secure_filename으로 파일명 정제
    secure_src = secure_filename(src)
    if not secure_src:
        return '<div class="error-embed">잘못된 비디오 파일명</div>'
    
    # 파일 확장자 검증
    allowed_video_extensions = {'mp4', 'webm', 'ogg', 'mov'}
    if not any(secure_src.lower().endswith(f".{ext}") for ext in allowed_video_extensions):
        return '<div class="error-embed">지원하지 않는 비디오 형식</div>'
    
    safe_src = escape(secure_src)
    safe_title = escape(title.strip()) if title and title.strip() else "비디오"
    safe_base_url = escape(base_url.rstrip('/'))
    
    ext = secure_src.split(".")[-1].lower()
    video_type = f"video/{ext}"
    if ext == "ogv": 
        video_type = "video/ogg"

    return f'''
<div class="video-container">
    <video controls preload="metadata" title="{safe_title}" class="text-post-video">
        <source src="{safe_base_url}/{safe_src}" type="{video_type}">
        브라우저가 비디오 재생을 지원하지 않습니다. <a href="{safe_base_url}/{safe_src}" download>비디오 다운로드</a>
    </video>
</div>
'''


def _create_audio_tag_secure(src: str, title: Optional[str], base_url: str) -> str:
    """안전한 오디오 태그 생성 - secure_filename 적용"""
    if not isinstance(src, str) or not src.strip():
        return '<div class="error-embed">오디오 경로가 없습니다</div>'
    
    src = src.strip()
    
    # secure_filename으로 파일명 정제
    secure_src = secure_filename(src)
    if not secure_src:
        return '<div class="error-embed">잘못된 오디오 파일명</div>'
    
    # 파일 확장자 검증
    allowed_audio_extensions = {'mp3', 'wav', 'ogg', 'flac', 'm4a'}
    if not any(secure_src.lower().endswith(f".{ext}") for ext in allowed_audio_extensions):
        return '<div class="error-embed">지원하지 않는 오디오 형식</div>'
    
    safe_src = escape(secure_src)
    safe_title = escape(title.strip()) if title and title.strip() else "오디오"
    safe_base_url = escape(base_url.rstrip('/'))

    ext = secure_src.split(".")[-1].lower()
    audio_type = f"audio/{ext}"
    if ext == "oga": 
        audio_type = "audio/ogg"

    return f'''
<div class="audio-container">
    <audio controls preload="metadata" title="{safe_title}" class="text-post-audio">
        <source src="{safe_base_url}/{safe_src}" type="{audio_type}">
        브라우저가 오디오 재생을 지원하지 않습니다. <a href="{safe_base_url}/{safe_src}" download>오디오 다운로드</a>
    </audio>
</div>
'''


def _create_quote_block(quote_text: str, author: Optional[str]) -> str:
    """인용구 블록 생성"""
    safe_quote = escape(quote_text.strip()) if quote_text else ""
    
    quote_html = f'<blockquote class="styled-quote">{safe_quote}'
    
    if author and author.strip():
        safe_author = escape(author.strip())
        quote_html += f'<span class="quote-author">{safe_author}</span>'
    
    quote_html += '</blockquote>'
    
    return quote_html


def _create_code_block(code_text: str, language: Optional[str]) -> str:
    """코드 블록 생성"""
    safe_code = escape(code_text) if code_text else ""
    
    # 언어 검증
    allowed_languages = {
        'python', 'javascript', 'html', 'css', 'sql', 'bash', 'shell',
        'json', 'xml', 'yaml', 'markdown', 'text', 'plaintext',
        'java', 'c', 'cpp', 'csharp', 'php', 'ruby', 'go', 'rust'
    }
    
    safe_language = 'plaintext'
    if language and language.strip().lower() in allowed_languages:
        safe_language = escape(language.strip().lower())
    
    return f'<pre><code class="language-{safe_language}">{safe_code}</code></pre>'


def _linkify_text_urls(text: str) -> str:
    """텍스트 내의 URL을 링크로 변환"""
    if not isinstance(text, str):
        return text
    
    # URL 패턴
    url_pattern = re.compile(
        r'\b(https?://[^\s<>"\'`\)]+)',
        re.IGNORECASE
    )
    
    def url_replacer(match):
        url = match.group(1)
        
        # URL 끝의 문장부호 제거
        url = url.rstrip('.,;:!?)]')
        
        # URL 길이 제한
        if len(url) > 1000:
            return match.group(0)
        
        # URL 안전성 검증
        if not _is_safe_url(url):
            return escape(match.group(0))
        
        # 안전한 URL로 이스케이프
        safe_url = escape(url)
        
        # 표시 텍스트 생성
        display_text = url
        if len(url) > 60:
            display_text = url[:57] + "..."
        
        # 링크 생성
        return (f'<a href="{safe_url}" '
                f'target="_blank" '
                f'rel="noopener noreferrer nofollow" '
                f'class="auto-link post-link"'
                f'title="{escape(url)}">{escape(display_text)}</a>')
    
    return url_pattern.sub(url_replacer, text)


def _auto_linkify_urls_safe(html_content: str) -> str:
    """HTML Parser를 사용한 안전한 URL 자동 링크 변환"""
    if not HTML_PARSER_ENABLED:
        return _auto_linkify_urls(html_content)
    
    try:
        parser = URLLinkifyParser()
        parser.feed(html_content)
        return ''.join(parser.result)
    except Exception as e:
        current_app.logger.error(f"HTML Parser 오류: {e}")
        return html_content


def _auto_linkify_urls(text: str) -> str:
    """URL 자동 링크 변환 - 폴백 버전"""
    if not isinstance(text, str):
        return text
    
    # 이미 링크가 있는지 확인
    if '<a ' in text and '</a>' in text:
        return text
    
    # 간단한 텍스트에만 URL 변환 적용
    return _linkify_text_urls(text)


def _is_safe_url(url: str) -> bool:
    """URL 안전성 검증"""
    if not url or not isinstance(url, str):
        return False
    
    # 위험한 프로토콜 차단
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    url_lower = url.lower()
    
    if any(url_lower.startswith(proto) for proto in dangerous_protocols):
        return False
    
    # HTTPS/HTTP만 허용
    if not url_lower.startswith(('http://', 'https://')):
        return False
    
    # 기본적인 URL 구조 확인
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return bool(parsed.netloc)
    except Exception:
        return False


def _process_markdown(content: str) -> str:
    """마크다운 처리"""
    try:
        # 마크다운 확장 프로그램 설정
        extensions = current_app.config.get('MARKDOWN_EXTENSIONS', [
            'extra', 'nl2br', 'sane_lists', 'codehilite', 'toc'
        ])
        
        # 마크다운 처리기 생성
        md = markdown.Markdown(
            extensions=extensions,
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                    'guess_lang': False,
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True,
                    'permalink_class': 'toc-link',
                    'permalink_title': '이 섹션에 대한 링크'
                }
            }
        )
        
        # HTML 변환
        html_content = md.convert(content)
        
        return html_content
        
    except Exception as e:
        current_app.logger.error(f"마크다운 처리 오류: {e}")
        return _process_content_fallback(content)


def _sanitize_html_preserve_links(html_content: str) -> str:
    """HTML 정제 - 링크 보존"""
    if not MARKDOWN_ENABLED:
        return html_content
    
    try:
        # 허용된 태그
        allowed_tags = current_app.config.get('ALLOWED_HTML_TAGS')
        
        # 허용된 속성
        allowed_attrs = current_app.config.get('ALLOWED_HTML_ATTRIBUTES')
        
        # HTML 정제
        clean_html = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            protocols=bleach.sanitizer.ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True
        )
        
        return clean_html
        
    except Exception as e:
        current_app.logger.error(f"HTML 정제 오류: {e}")
        return escape(html_content)


def _process_content_fallback(content: str) -> str:
    """마크다운 라이브러리 없을 때 기본 처리"""
    lines = content.split('\n')
    processed_lines = []
    in_code_block = False
    current_paragraph = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 빈 줄 처리
        if not line_stripped:
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            processed_lines.append('<br>')
            continue
        
        # 코드 블록 처리
        if line_stripped.startswith('```'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
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
        
        # 헤더 처리
        if line_stripped.startswith('#'):
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph)
                processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
                current_paragraph = []
            
            header_match = re.match(r'^(#+)\s+(.+)$', line_stripped)
            if header_match:
                level = min(max(len(header_match.group(1)), 1), 6)
                header_text = escape(header_match.group(2))
                header_id = re.sub(r'[^\w가-힣\-]', '-', header_text.lower())[:50]
                processed_lines.append(f'<h{level} id="{header_id}">{header_text}</h{level}>')
                continue
        
        # 일반 텍스트
        current_paragraph.append(escape(line_stripped))
    
    # 마지막 단락 처리
    if current_paragraph:
        paragraph_text = " ".join(current_paragraph)
        processed_lines.append(f'<p class="compact-text">{paragraph_text}</p>')
    
    return '\n'.join(processed_lines)
