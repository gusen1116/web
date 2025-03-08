// toolbar-manager.js
import Utils from './utils.js';

class ToolbarManager {
    constructor(contentArea) {
        // 직접 요소만 저장 (순환 참조 없음)
        this.contentArea = contentArea;
        this.toolbarButtons = document.querySelectorAll('.toolbar-button');
        
        // 텍스트 크기 조절 상태 초기화
        this.currentFontSize = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--content-font-size') || '16px');
        
        // 툴바가 있는 경우에만 이벤트 바인딩
        if (this.toolbarButtons && this.toolbarButtons.length > 0) {
            this.bindEvents();
        }
    }
    
    bindEvents() {
        this.toolbarButtons.forEach(button => {
            const command = button.dataset.command;
            if (!command) return;
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleToolbarAction(command, button.dataset.value);
            });
        });
        
        // 콘텐츠 영역 키보드 이벤트 처리
        if (this.contentArea) {
            const throttledKeyHandler = Utils.throttle(this.handleKeyDown.bind(this), 100);
            this.contentArea.addEventListener('keydown', throttledKeyHandler);
            
            // 붙여넣기 이벤트 처리
            this.contentArea.addEventListener('paste', this.handlePaste.bind(this));
        }
        
        // 텍스트 크기 조절 버튼 이벤트 바인딩
        const textSizeButtons = document.querySelectorAll('.text-size-control');
        if (textSizeButtons && textSizeButtons.length > 0) {
            textSizeButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    const size = button.dataset.size;
                    if (size) {
                        this.adjustTextSize(size);
                        
                        // 활성 상태 업데이트
                        textSizeButtons.forEach(btn => btn.classList.remove('active'));
                        button.classList.add('active');
                    }
                });
            });
            
            // 저장된 선호도 불러오기
            const savedSize = localStorage.getItem('preferredTextSize');
            if (savedSize) {
                this.adjustTextSize(savedSize);
                textSizeButtons.forEach(button => {
                    if (button.dataset.size === savedSize) {
                        button.classList.add('active');
                    }
                });
            } else {
                // 기본 크기 버튼 활성화
                const defaultButton = document.querySelector('.text-size-control[data-size="16px"]');
                if (defaultButton) {
                    defaultButton.classList.add('active');
                }
            }
        }
    }
    
    handleToolbarAction(command, value) {
        // 콘텐츠 영역 확인 - 없으면 명령 실행 불가
        if (!this.contentArea) {
            console.error('콘텐츠 영역이 없어 명령을 실행할 수 없습니다.');
            return;
        }
        
        switch(command) {
            case 'formatBlock':
                document.execCommand('formatBlock', false, value);
                break;
            case 'insertImage':
                this.handleImageInsertion();
                break;
            case 'createLink':
                this.handleLinkInsertion();
                break;
            case 'foreColor':
                this.applyColorStyle();
                break;
            case 'hiliteColor':
                this.applyBackgroundColor();
                break;
            case 'insertTable':
                this.insertTable();
                break;
            case 'insertEmoji':
                const throttledInsertEmoji = Utils.throttle(this.insertEmoji.bind(this), 300);
                throttledInsertEmoji();
                break;
            case 'insertCodeBlock':
                this.insertCodeBlock();
                break;
            case 'resizeImage':
                this.resizeSelectedImage();
                break;
            case 'adjustTextSize':
                this.adjustTextSize(value);
                break;
            default:
                // 기본 명령 실행
                document.execCommand(command, false, value);
                break;
        }
        
        // 안전하게 포커스 되돌리기
        try {
            this.contentArea.focus();
        } catch (e) {
            console.error('포커스 설정 오류:', e);
        }
    }
    
    // 텍스트 크기 조절 메서드
    adjustTextSize(size) {
        if (!size) return;
        
        // CSS 변수를 통해 전역적으로 글자 크기 적용
        document.documentElement.style.setProperty('--content-font-size', size);
        
        // 현재 크기 업데이트
        this.currentFontSize = parseInt(size);
        
        // 사용자 선호도 저장
        localStorage.setItem('preferredTextSize', size);
        
        // 콘텐츠 컨테이너 최소 너비 조정 (반응형)
        const contentContainer = document.querySelector('.content-container');
        if (contentContainer) {
            const viewportWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
            
            // 화면 크기에 따라 최소 너비 조정
            if (viewportWidth > 1024) {  // 데스크톱
                contentContainer.style.minWidth = 'min(60vw, 500px)';
            } else if (viewportWidth > 768) {  // 태블릿
                contentContainer.style.minWidth = 'min(80vw, 500px)';
            } else {  // 모바일
                contentContainer.style.minWidth = '90vw';
            }
        }
        
        console.log('글자 크기가 변경되었습니다:', size);
    }
    
    handleKeyDown(e) {
        // 콘텐츠 영역 확인
        if (!this.contentArea) return;
        
        // 탭 키 처리
        if (e.key === 'Tab') {
            e.preventDefault();
            document.execCommand('insertText', false, '    ');
        }
        
        // Enter 키 처리
        if (e.key === 'Enter' && !e.shiftKey) {
            // 현재 선택 영역 가져오기
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            
            // 코드 블록 내부에서는 기본 동작 유지
            if (this.isInsideCodeBlock(range.startContainer)) {
                return;
            }
            
            // 목록 항목에서는 기본 동작 유지
            const currentBlock = this.getParentBlockElement(range.startContainer);
            if (currentBlock && (
                currentBlock.tagName === 'LI' || 
                (currentBlock.parentElement && 
                (currentBlock.parentElement.tagName === 'UL' || 
                currentBlock.parentElement.tagName === 'OL'))
            )) {
                return;
            }
            
            // 제목에서 Enter를 누르면 새 단락으로
            if (currentBlock && /^H[1-6]$/.test(currentBlock.tagName)) {
                e.preventDefault();
                document.execCommand('insertParagraph');
                return;
            }
        }
    }
    
    handlePaste(e) {
        if (!this.contentArea) return;
        
        e.preventDefault();
        
        // 붙여넣은 텍스트 확인
        const clipboardText = e.clipboardData.getData('text/plain');
        const pasteHTML = e.clipboardData.getData('text/html');
        
        // 미디어 URL인지 확인
        if (clipboardText && clipboardText.trim()) {
            // URL 패턴 검사 로직 (실제 구현에서는 더 복잡할 수 있음)
            if (this.handleMediaEmbed(clipboardText)) {
                return; // 미디어로 처리됨
            }
        }
        
        // HTML 붙여넣기 처리
        if (pasteHTML) {
            // HTML 정리 (불필요한 스타일 및 위험 요소 제거)
            const cleanHTML = Utils.sanitizeHTML(pasteHTML);
            document.execCommand('insertHTML', false, cleanHTML);
        } else {
            // 텍스트만 있는 경우
            document.execCommand('insertText', false, clipboardText);
        }
    }
    
    handleMediaEmbed(url) {
        // 미디어 임베드 처리 함수 (실제 구현은 미디어 타입에 따라 다름)
        // 예시로 빈 함수 구현
        return false;
    }
    
    // 이미지가 코드 블록 내에 있는지 확인
    isInsideCodeBlock(node) {
        while (node && node !== this.contentArea) {
            if (node.nodeName === 'PRE' || node.nodeName === 'CODE') {
                return true;
            }
            node = node.parentNode;
        }
        return false;
    }
    
    // 부모 블록 요소 찾기
    getParentBlockElement(node) {
        while (node && node !== this.contentArea) {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const display = window.getComputedStyle(node).display;
                if (display === 'block' || display === 'list-item') {
                    return node;
                }
            }
            node = node.parentNode;
        }
        return null;
    }
    
    // 색상 선택기 표시
    applyColorStyle() {
        if (!this.contentArea) return;
        
        // 색상 선택기 생성
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = '#000000';
        
        try {
            // 선택기 표시
            colorPicker.click();
            
            // 색상 변경 이벤트
            colorPicker.addEventListener('change', function() {
                document.execCommand('foreColor', false, this.value);
            });
        } catch (e) {
            console.error('색상 선택기 오류:', e);
            // 실패 시 간단한 팝업으로 대체
            const color = prompt('색상 코드를 입력하세요 (예: #FF0000):', '#000000');
            if (color) {
                document.execCommand('foreColor', false, color);
            }
        }
    }
    
    // 배경색 선택기 표시
    applyBackgroundColor() {
        if (!this.contentArea) return;
        
        // 색상 선택기 생성
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = '#FFFF00';
        
        try {
            // 선택기 표시
            colorPicker.click();
            
            // 색상 변경 이벤트
            colorPicker.addEventListener('change', function() {
                document.execCommand('hiliteColor', false, this.value);
            });
        } catch (e) {
            console.error('배경색 선택기 오류:', e);
            // 실패 시 간단한 팝업으로 대체
            const color = prompt('배경색 코드를 입력하세요 (예: #FFFF00):', '#FFFF00');
            if (color) {
                document.execCommand('hiliteColor', false, color);
            }
        }
    }
    
    handleLinkInsertion() {
        if (!this.contentArea) return;
        
        const selection = window.getSelection();
        if (!selection) return;
        
        const selectedText = selection.toString();
        
        // 링크 URL 입력 받기
        const url = prompt('링크 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
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
    
    handleImageInsertion() {
        // 이미지 삽입 기능 (실제 구현 필요)
        alert('이미지 삽입 기능이 아직 구현되지 않았습니다.');
    }
    
    insertTable() {
        if (!this.contentArea) return;
        
        const rows = prompt('행 수를 입력하세요:', '3');
        const cols = prompt('열 수를 입력하세요:', '3');
        
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
    
    insertCodeBlock() {
        if (!this.contentArea) return;
        
        const language = prompt('프로그래밍 언어를 입력하세요 (예: javascript, python):', 'javascript');
        
        if (language) {
            const codeBlockHTML = `<pre><code class="language-${language}">여기에 코드를 입력하세요</code></pre>`;
            document.execCommand('insertHTML', false, codeBlockHTML);
            
            // 코드 블록 내부로 커서 이동
            try {
                const selection = window.getSelection();
                if (!selection) return;
                
                const range = document.createRange();
                const codeElement = this.contentArea.querySelector('code:last-of-type');
                
                if (codeElement) {
                    range.selectNodeContents(codeElement);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            } catch (e) {
                console.error('코드 블록 커서 설정 오류:', e);
            }
        }
    }
    
    resizeSelectedImage() {
        if (!this.contentArea) return;
        
        // 선택된 이미지 찾기
        const selectedImage = this.contentArea.querySelector('img.selected');
        if (!selectedImage) {
            alert('이미지를 먼저 선택해주세요.');
            return;
        }
        
        // 이미지 크기 조정 로직
        const width = prompt('너비를 입력하세요 (픽셀):', selectedImage.width);
        if (width) {
            selectedImage.style.width = width + 'px';
        }
    }
    
    insertEmoji() {
        if (!this.contentArea) return;
        
        const commonEmojis = ['😀', '😊', '👍', '👏', '🙏', '💪', '👀', '🧠', '💡', '📝'];
        let html = '<div class="emoji-picker">';
        
        commonEmojis.forEach(emoji => {
            html += `<span class="emoji-option" data-emoji="${emoji}">${emoji}</span>`;
        });
        
        html += '</div>';
        
        // 이모지 선택기 컨테이너 생성
        const container = document.createElement('div');
        container.className = 'emoji-picker-container';
        container.innerHTML = html;
        document.body.appendChild(container);
        
        // 이모지 클릭 이벤트
        container.querySelectorAll('.emoji-option').forEach(option => {
            option.addEventListener('click', () => {
                const emoji = option.dataset.emoji;
                document.execCommand('insertText', false, emoji);
                container.remove();
            });
        });
        
        // 외부 클릭 시 선택기 닫기
        document.addEventListener('click', function closeEmojiPicker(e) {
            if (!container.contains(e.target)) {
                container.remove();
                document.removeEventListener('click', closeEmojiPicker);
            }
        });
    }
}

export default ToolbarManager;