// embed-handler.js
class EmbedHandler {
    constructor(contentArea) {
        this.contentArea = contentArea;
    }
    
    insertIframe() {
        if (!this.contentArea) return;
        
        const url = prompt('임베드할 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
            // YouTube URL인지 확인하고 임베드 URL로 변환
            let finalUrl = url;
            let isYouTube = false;
            
            // YouTube 동영상 URL 변환
            const youtubeRegex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/i;
            const youtubeMatch = url.match(youtubeRegex);
            
            if (youtubeMatch && youtubeMatch[1]) {
                finalUrl = `https://www.youtube.com/embed/${youtubeMatch[1]}`;
                isYouTube = true;
            }
            
            // 기본 iframe 크기
            // YouTube의 경우 16:9 비율로 설정
            let width = '100%';
            let height = isYouTube ? '0' : '400px'; // YouTube는 padding-top으로 비율 유지
            
            // 사용자 크기 입력 옵션
            const customSize = confirm('iframe 크기를 직접 지정하시겠습니까?');
            
            const finalWidth = customSize ? 
                prompt('너비를 입력하세요 (예: 500px 또는 100%):', width) : width;
            
            const finalHeight = customSize ? 
                prompt('높이를 입력하세요 (예: 400px):', isYouTube ? '315px' : height) : height;
            
            // iframe 생성 - 보안 강화된 sandbox 속성 추가
            let iframeHTML;
            
            if (isYouTube && !customSize) {
                // YouTube용 반응형 16:9 컨테이너
                iframeHTML = `
                    <div class="iframe-embed-container">
                        <div class="responsive-video-container">
                            <iframe 
                                src="${finalUrl}" 
                                allowfullscreen 
                                loading="lazy"
                                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation"
                                referrerpolicy="no-referrer-when-downgrade">
                            </iframe>
                        </div>
                        <div class="embed-caption" contenteditable="true">YouTube 동영상</div>
                    </div>
                `;
            } else {
                // 일반 iframe 또는 사용자 지정 크기
                iframeHTML = `
                    <div class="iframe-embed-container">
                        <iframe 
                            src="${finalUrl}" 
                            style="width: ${finalWidth}; height: ${finalHeight}; border: 1px solid #ddd;" 
                            allowfullscreen 
                            loading="lazy"
                            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation"
                            referrerpolicy="no-referrer-when-downgrade">
                        </iframe>
                        <div class="embed-caption" contenteditable="true">${isYouTube ? 'YouTube 동영상' : 'iframe 임베드'} (더블클릭으로 편집)</div>
                    </div>
                `;
            }
            
            document.execCommand('insertHTML', false, iframeHTML);
        }
    }
    
    // 기존 임베드 수정
    editEmbed(embedContainer) {
        if (!embedContainer) return;
        
        const iframe = embedContainer.querySelector('iframe');
        if (!iframe) return;
        
        // 현재 값 가져오기
        const currentSrc = iframe.src;
        const currentWidth = iframe.style.width;
        const currentHeight = iframe.style.height;
        
        // 사용자 입력 받기
        const newSrc = prompt('URL을 수정하세요:', currentSrc);
        if (!newSrc) return;
        
        // YouTube URL인지 확인하고 임베드 URL로 변환
        let finalUrl = newSrc;
        let isYouTube = false;
        
        // YouTube 동영상 URL 변환
        const youtubeRegex = /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/i;
        const youtubeMatch = newSrc.match(youtubeRegex);
        
        if (youtubeMatch && youtubeMatch[1]) {
            finalUrl = `https://www.youtube.com/embed/${youtubeMatch[1]}`;
            isYouTube = true;
        }
        
        const newWidth = prompt('너비를 수정하세요 (예: 500px 또는 100%):', currentWidth);
        const newHeight = prompt('높이를 수정하세요 (예: 400px):', currentHeight);
        
        // 값 업데이트 - 변환된 URL 사용
        iframe.src = finalUrl;
        iframe.style.width = newWidth;
        iframe.style.height = newHeight;
        
        // 캡션 업데이트
        const caption = embedContainer.querySelector('.embed-caption');
        if (caption && isYouTube) {
            caption.textContent = 'YouTube 동영상 (더블클릭으로 편집)';
        }
    }
}

export default EmbedHandler;