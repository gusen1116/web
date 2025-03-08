// MediaHandler.js
import Utils from "./utils.js";

class MediaHandler {
    constructor(editor) {
        this.editor = editor;
        this.MEDIA_PATTERNS = [
            // YouTube
            {
                regex: /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/i,
                handler: (match) => {
                    const videoId = match[1];
                    return `<div class="media-embed youtube-embed">
                        <iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId}" 
                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; 
                        gyroscope; picture-in-picture" allowfullscreen></iframe>
                        <div class="embed-caption">YouTube 동영상</div>
                    </div>`;
                }
            },
            // Twitch
            {
                regex: /(?:https?:\/\/)?(?:www\.)?(?:twitch\.tv\/videos\/)(\d+)/i,
                handler: (match) => {
                    const videoId = match[1];
                    return `<div class="media-embed twitch-embed">
                        <iframe src="https://player.twitch.tv/?video=${videoId}&parent=${window.location.hostname}" 
                        frameborder="0" allowfullscreen="true" scrolling="no" height="315" width="560"></iframe>
                        <div class="embed-caption">Twitch 동영상</div>
                    </div>`;
                }
            },
            // Twitter
            {
                regex: /(?:https?:\/\/)?(?:www\.)?twitter\.com\/(?:\w+)\/status\/(\d+)/i,
                handler: (match) => {
                    const tweetId = match[1];
                    return `<div class="media-embed twitter-embed" data-tweet-id="${tweetId}">
                        <blockquote class="twitter-tweet" data-dnt="true">
                            <a href="https://twitter.com/x/status/${tweetId}"></a>
                        </blockquote>
                        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                        <div class="embed-caption">Twitter 포스트</div>
                    </div>`;
                }
            }
        ];
    }
    
    handleImageInsertion() {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.click();
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files && fileInput.files[0]) {
                this.uploadImage(fileInput.files[0]);
            }
        });
    }
    
    uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        // 진행 표시기
        const progressIndicator = document.createElement('div');
        progressIndicator.className = 'upload-progress';
        progressIndicator.innerHTML = '<span>이미지 업로드 중...</span>';
        progressIndicator.setAttribute('aria-live', 'assertive');
        document.body.appendChild(progressIndicator);
        
        // CSRF 토큰 가져오기
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
        
        if (!csrfToken) {
            console.error('CSRF 토큰을 찾을 수 없습니다.');
            progressIndicator.remove();
            alert('보안 토큰을 찾을 수 없습니다. 페이지를 새로고침해 주세요.');
            return;
        }
        
        // 서버에 업로드
        fetch('/blog/upload', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`서버 응답 오류: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            progressIndicator.remove();
            
            if (data.success === 1) {
                // 이미지 삽입 (크기 속성 추가)
                const imgHtml = `<img src="${data.file.url}" alt="업로드된 이미지" class="editor-image" style="max-width: 100%;" contenteditable="true">`;
                document.execCommand('insertHTML', false, imgHtml);
                
                // 방금 삽입된 이미지에 이벤트 리스너 추가
                setTimeout(() => {
                    const lastImage = this.editor.contentArea.querySelector('img:last-child');
                    if (lastImage) {
                        // 이미 선택된 이미지 클래스 제거
                        const allImages = this.editor.contentArea.querySelectorAll('img');
                        allImages.forEach(img => img.classList.remove('selected'));
                        
                        // 새 이미지 선택 표시
                        lastImage.classList.add('selected');
                        
                        // 크기 조절 가능하도록 속성 추가
                        lastImage.setAttribute('contenteditable', 'true');
                        
                        // 크기 조절 안내 메시지
                        alert('이미지가 삽입되었습니다. 크기를 조절하려면 이미지를 선택한 후 "이미지 크기 조절" 버튼을 클릭하세요.');
                    }
                }, 100);
            } else {
                alert('이미지 업로드 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            progressIndicator.remove();
            console.error('업로드 오류:', error);
            alert('이미지 업로드 중 오류가 발생했습니다.');
        });
    }
}

export default MediaHandler;