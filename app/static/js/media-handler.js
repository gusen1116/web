// media-handler.js
class MediaHandler {
    constructor(contentArea) {
        // EditorCore 참조 대신 필요한 DOM 요소만 전달받음
        this.contentArea = contentArea;
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
                    if (!this.contentArea) return;
                    
                    const lastImage = this.contentArea.querySelector('img:last-child');
                    if (lastImage) {
                        // 이미 선택된 이미지 클래스 제거
                        const allImages = this.contentArea.querySelectorAll('img');
                        allImages.forEach(img => img.classList.remove('selected'));
                        
                        // 새 이미지 선택 표시
                        lastImage.classList.add('selected');
                        
                        // 크기 조절 가능하도록 속성 추가
                        lastImage.setAttribute('contenteditable', 'true');
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
    
    handleMediaEmbed(url) {
        if (!url || !this.contentArea) return false;
        
        for (const pattern of this.MEDIA_PATTERNS) {
            if (pattern.regex.test(url)) {
                const match = url.match(pattern.regex);
                if (match) {
                    const embedHtml = pattern.handler(match);
                    document.execCommand('insertHTML', false, embedHtml);
                    return true;
                }
            }
        }
        
        return false;
    }
    
    handleLinkInsertion() {
        const selection = window.getSelection();
        if (!selection || !this.contentArea) return;
        
        const selectedText = selection.toString();
        
        // 링크 URL 입력 받기
        const url = prompt('링크 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
            // 먼저 미디어 임베드인지 확인
            if (this.handleMediaEmbed(url)) {
                return; // 미디어로 처리됨
            }
            
            if (selectedText) {
                // 선택한 텍스트에 링크 적용
                document.execCommand('createLink', false, url);
                
                // 새 창에서 열리도록 타겟 속성 추가
                const links = this.contentArea.querySelectorAll('a[href="' + url + '"]');
                links.forEach(link => {
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                });
            } else {
                // 선택한 텍스트가 없으면 새 링크 텍스트 입력 받기
                const linkText = prompt('링크 텍스트를 입력하세요:', '');
                if (linkText) {
                    const linkHtml = `<a href="${url}" target="_blank" rel="noopener noreferrer">${linkText}</a>`;
                    document.execCommand('insertHTML', false, linkHtml);
                }
            }
        }
    }
    
    insertTable(rows, cols) {
        if (!this.contentArea) return;
        
        if (!rows || !cols) {
            rows = prompt('행 수를 입력하세요:', '3');
            cols = prompt('열 수를 입력하세요:', '3');
        }
        
        if (rows && cols) {
            const numRows = parseInt(rows);
            const numCols = parseInt(cols);
            
            if (numRows > 0 && numCols > 0) {
                let tableHTML = '<table class="editor-table"><tbody>';
                
                // 헤더 행 생성
                tableHTML += '<tr>';
                for (let j = 0; j < numCols; j++) {
                    tableHTML += `<th>헤더 ${j+1}</th>`;
                }
                tableHTML += '</tr>';
                
                // 데이터 행 생성
                for (let i = 0; i < numRows - 1; i++) {
                    tableHTML += '<tr>';
                    for (let j = 0; j < numCols; j++) {
                        tableHTML += `<td>셀 ${i+1}-${j+1}</td>`;
                    }
                    tableHTML += '</tr>';
                }
                
                tableHTML += '</tbody></table>';
                
                document.execCommand('insertHTML', false, tableHTML);
            }
        }
    }
    
    resizeSelectedImage() {
        if (!this.contentArea) return;
        
        const selectedImage = this.contentArea.querySelector('img.selected');
        if (!selectedImage) {
            alert('먼저 이미지를 선택해주세요.');
            return;
        }
        
        // 현재 크기 가져오기
        const currentWidth = selectedImage.width;
        const currentHeight = selectedImage.height;
        
        // 새 크기 입력 받기
        const newWidth = prompt('너비를 입력하세요 (픽셀):', currentWidth);
        if (newWidth === null) return; // 취소된 경우
        
        // 비율 계산
        const ratio = currentHeight / currentWidth;
        const calculatedHeight = Math.round(parseInt(newWidth) * ratio);
        
        // 높이 입력 받기 (계산된 값을 기본값으로)
        const newHeight = prompt('높이를 입력하세요 (픽셀):', calculatedHeight);
        if (newHeight === null) return; // 취소된 경우
        
        // 이미지 크기 변경
        selectedImage.style.width = newWidth + 'px';
        selectedImage.style.height = newHeight + 'px';
        
        // 속성 업데이트를 위한 추가 작업 (선택 사항)
        selectedImage.setAttribute('width', newWidth);
        selectedImage.setAttribute('height', newHeight);
    }
}

export default MediaHandler;