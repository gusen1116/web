// ToolbarManager.js
import Utils from './Utils.js';
import MediaHandler from './MediaHandler.js';

class ToolbarManager {
    constructor(editor) {
        this.editor = editor;
        this.toolbarButtons = document.querySelectorAll('.toolbar-button');
        this.mediaHandler = new MediaHandler(editor);
        this.bindEvents();
    }
    
    bindEvents() {
        if (this.toolbarButtons && this.toolbarButtons.length > 0) {
            this.toolbarButtons.forEach(button => {
                const command = button.dataset.command;
                if (!command) return;
                
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleToolbarAction(command, button.dataset.value);
                });
            });
        }
        
        // 콘텐츠 영역 키보드 이벤트 처리
        if (this.editor.contentArea) {
            const throttledKeyHandler = Utils.throttle(this.handleKeyDown.bind(this), 100);
            this.editor.contentArea.addEventListener('keydown', throttledKeyHandler);
        }
        
        // 붙여넣기 이벤트 처리
        if (this.editor.contentArea) {
            this.editor.contentArea.addEventListener('paste', this.handlePaste.bind(this));
        }
    }
    
    handleToolbarAction(command, value) {
        switch(command) {
            case 'formatBlock':
                document.execCommand('formatBlock', false, value);
                break;
            case 'insertImage':
                this.mediaHandler.handleImageInsertion();
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
            default:
                // 기본 명령 실행
                document.execCommand(command, false, null);
                break;
        }
        
        // 포커스 되돌리기
        this.editor.contentArea.focus();
    }
    
    handleKeyDown(e) {
        // 탭 키 처리
        if (e.key === 'Tab') {
            e.preventDefault();
            document.execCommand('insertText', false, '    ');
        }
        
        // Enter 키로 새 단락 생성 관련 처리
        if (e.key === 'Enter' && !e.shiftKey) {
            const selection = window.getSelection();
            if (!selection || selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            const currentBlock = this.editor.contentManager.getParentBlockElement(range.startContainer);
            
            // 코드 블록 내부에서는 기본 동작 유지
            if (this.editor.contentManager.isInsideCodeBlock(range.startContainer)) {
                return;
            }
            
            // 목록 항목에서는 기본 동작 유지
            if (currentBlock && (currentBlock.tagName === 'LI' || 
                                currentBlock.parentElement && 
                                (currentBlock.parentElement.tagName === 'UL' || 
                                currentBlock.parentElement.tagName === 'OL'))) {
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
        e.preventDefault();
        
        // 붙여넣은 텍스트 확인
        const clipboardText = e.clipboardData.getData('text/plain');
        let pasteHTML = e.clipboardData.getData('text/html');
        
        // 미디어 URL인지 확인 및 처리
        if (clipboardText && clipboardText.trim()) {
            let isMediaUrl = false;
            
            for (const pattern of this.mediaHandler.MEDIA_PATTERNS) {
                if (pattern.regex.test(clipboardText)) {
                    // 선택 영역 삭제
                    const selection = window.getSelection();
                    if (selection && selection.rangeCount > 0) {
                        const range = selection.getRangeAt(0);
                        range.deleteContents();
                        
                        // 임베드 HTML 삽입
                        const embedHtml = pattern.handler(clipboardText.match(pattern.regex));
                        const fragment = document.createDocumentFragment();
                        const div = document.createElement('div');
                        div.innerHTML = embedHtml;
                        
                        while (div.firstChild) {
                            fragment.appendChild(div.firstChild);
                        }
                        
                        range.insertNode(fragment);
                        range.collapse(false);
                    }
                    
                    isMediaUrl = true;
                    break;
                }
            }
            
            if (isMediaUrl) {
                return; // 미디어 URL이 처리되었으므로 기본 붙여넣기 처리 중단
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
    
    handleLinkInsertion() {
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
                const links = this.editor.contentArea.querySelectorAll('a[href="' + url + '"]');
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
    
    applyColorStyle() {
        const color = prompt('색상 코드를 입력하세요 (예: #FF0000 또는 red):', '');
        if (color) {
            document.execCommand('foreColor', false, color);
        }
    }
    
    applyBackgroundColor() {
        const color = prompt('배경색 코드를 입력하세요 (예: #FFFF00 또는 yellow):', '');
        if (color) {
            document.execCommand('hiliteColor', false, color);
        }
    }
    
    insertTable() {
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
    
    insertEmoji() {
        const commonEmojis = [
            '😀', '😁', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😊', 
            '😋', '😎', '😍', '😘', '😗', '😙', '😚', '🙂', '🤔', '😐', 
            '😑', '😶', '🙄', '😏', '😣', '😥', '😮', '🤐', '😯', '😪', 
            '😫', '😴', '😌', '😛', '😜', '😝', '🤤', '😒', '😓', '😔'
        ];
        
        let emojiPickerHTML = '<div class="emoji-picker">';
        commonEmojis.forEach(emoji => {
            emojiPickerHTML += `<span class="emoji-option" data-emoji="${emoji}" role="button" tabindex="0">${emoji}</span>`;
        });
        emojiPickerHTML += '</div>';
        
        // 이모지 선택기 추가
        const emojiPicker = document.createElement('div');
        emojiPicker.className = 'emoji-picker-container';
        emojiPicker.innerHTML = emojiPickerHTML;
        document.body.appendChild(emojiPicker);
        
        // 이모지 클릭 이벤트 처리
        const emojiOptions = emojiPicker.querySelectorAll('.emoji-option');
        emojiOptions.forEach(option => {
            option.addEventListener('click', function() {
                const emoji = this.dataset.emoji;
                document.execCommand('insertText', false, emoji);
                emojiPicker.remove();
            });
            
            // 키보드 접근성 추가
            option.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const emoji = this.dataset.emoji;
                    document.execCommand('insertText', false, emoji);
                    emojiPicker.remove();
                }
            });
        });
        
        // 외부 클릭 시 이모지 선택기 닫기
        document.addEventListener('click', function closeEmojiPicker(e) {
            if (!emojiPicker.contains(e.target) && e.target !== document.querySelector('[data-command="insertEmoji"]')) {
                emojiPicker.remove();
                document.removeEventListener('click', closeEmojiPicker);
            }
        });
    }
    
    insertCodeBlock() {
        const language = prompt('프로그래밍 언어를 입력하세요 (예: javascript, python):', 'javascript');
        
        if (language) {
            const codeBlockHTML = `<pre><code class="language-${language}">여기에 코드를 입력하세요</code></pre>`;
            document.execCommand('insertHTML', false, codeBlockHTML);
            
            // 코드 블록 내부로 커서 이동 및 선택
            const selection = window.getSelection();
            if (!selection) return;
            
            const range = document.createRange();
            const codeElement = this.editor.contentArea.querySelector('code:last-of-type');
            
            if (codeElement) {
                range.selectNodeContents(codeElement);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
    }
}

export default ToolbarManager;