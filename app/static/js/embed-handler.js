// embed-handler.js
class EmbedHandler {
    constructor(contentArea) {
        this.contentArea = contentArea;
    }
    
    insertIframe() {
        if (!this.contentArea) return;
        
        const url = prompt('임베드할 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
            // 기본 iframe 크기
            const width = '100%';
            const height = '400px';
            
            // 사용자 크기 입력 옵션
            const customSize = confirm('iframe 크기를 직접 지정하시겠습니까?');
            
            const finalWidth = customSize ? 
                prompt('너비를 입력하세요 (예: 500px 또는 100%):', width) : width;
                
            const finalHeight = customSize ? 
                prompt('높이를 입력하세요 (예: 400px):', height) : height;
            
            // iframe 생성
            const iframeHTML = `
                <div class="iframe-embed-container" style="position: relative; overflow: hidden; margin: 1em 0;">
                    <iframe 
                        src="${url}" 
                        style="width: ${finalWidth}; height: ${finalHeight}; border: 1px solid #ddd;" 
                        allowfullscreen 
                        loading="lazy"
                        sandbox="allow-scripts allow-same-origin allow-forms">
                    </iframe>
                    <div class="embed-caption" contenteditable="true">iframe 임베드 (더블클릭으로 편집)</div>
                </div>
            `;
            
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
        
        const newWidth = prompt('너비를 수정하세요 (예: 500px 또는 100%):', currentWidth);
        const newHeight = prompt('높이를 수정하세요 (예: 400px):', currentHeight);
        
        // 값 업데이트
        iframe.src = newSrc;
        iframe.style.width = newWidth;
        iframe.style.height = newHeight;
    }
}

export default EmbedHandler;