document.addEventListener('DOMContentLoaded', function() {
    // 기본 요소 참조
    const contentArea = document.getElementById('content-area');
    const titleInput = document.getElementById('post-title');
    const categorySelect = document.getElementById('post-category');
    const tagsInput = document.getElementById('post-tags');
    const saveButton = document.getElementById('save-post');
    const toolbarButtons = document.querySelectorAll('.toolbar-button');
    const editorContainer = document.getElementById('editor-container');
    
    // 제목 입력 유도 UI 요소 생성
    const titleFeedback = document.createElement('div');
    titleFeedback.className = 'input-feedback';
    titleFeedback.style.color = '#d73a49';
    titleFeedback.style.fontSize = '0.9em';
    titleFeedback.style.marginTop = '5px';
    titleFeedback.style.display = 'none';
    if (titleInput && titleInput.parentNode) {
        titleInput.parentNode.appendChild(titleFeedback);
    }
    
    // 자동 저장 관련 변수 및 기능
    let autoSaveInterval;
    let lastSavedContent = '';
    const AUTO_SAVE_DELAY = 15000; // 15초마다 자동 저장
    
    // 미디어 임베드 패턴 및 처리 함수
    const MEDIA_PATTERNS = [
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
    
    const Utils = {
        throttle(func, delay) {
            let lastCall = 0;
            return function(...args) {
                const now = new Date().getTime();
                if (now - lastCall < delay) {
                    return;
                }
                lastCall = now;
                return func(...args);
            }
        }
    };
    
    // CSV 파싱 함수
    function parseCSV(csvText) {
        const lines = csvText.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];
        
        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim() === '') continue;
            
            const values = lines[i].split(',');
            const row = {};
            
            for (let j = 0; j < headers.length; j++) {
                row[headers[j]] = values[j]?.trim() || '';
            }
            
            data.push(row);
        }
        
        return data;
    }
    
    // 기존 콘텐츠 로드 함수
    function loadExistingContent() {
        const existingContent = document.getElementById('existing-content');
        if (existingContent && existingContent.textContent.trim()) {
            try {
                const contentObj = JSON.parse(existingContent.textContent);
                renderContent(contentObj);
            } catch (e) {
                console.error('콘텐츠 파싱 오류:', e);
                contentArea.innerHTML = existingContent.textContent;
            }
        }
    }
    
    // 툴바 선택 박스 이벤트 처리
    const toolbarSelects = document.querySelectorAll('.toolbar-select');
    if (toolbarSelects && toolbarSelects.length > 0) {
        toolbarSelects.forEach(select => {
            const command = select.dataset.command;
            if (!command) return;
            
            select.addEventListener('change', function() {
                const value = this.value;
                if (!value) return;
                
                switch(command) {
                    case 'fontSize':
                        document.execCommand(command, false, value);
                        break;
                    default:
                        document.execCommand(command, false, value);
                        break;
                }
                
                // 선택 후 기본값으로 복원
                this.selectedIndex = 0;
                
                // 포커스 되돌리기
                contentArea.focus();
            });
        });
    }

    // 이미지 선택 이벤트
    if (contentArea) {
        contentArea.addEventListener('click', function(e) {
            // 이미 선택된 이미지 클래스 제거
            const allImages = this.querySelectorAll('img');
            allImages.forEach(img => img.classList.remove('selected'));
            
            // 클릭한 요소가 이미지인 경우
            if (e.target.tagName === 'IMG') {
                e.target.classList.add('selected');
                
                // 이미지에 크기 조절 속성 추가
                if (!e.target.getAttribute('contenteditable')) {
                    e.target.setAttribute('contenteditable', 'true');
                }
            }
        });
    }
    
    // 로컬 스토리지에 콘텐츠 저장
    function saveContentToLocalStorage(title, content) {
        if (!editorContainer) return; // 에디터 컨테이너가 없으면 저장하지 않음
        
        const postId = editorContainer.dataset.postId;
        const storageKey = postId ? `autosave_post_${postId}` : 'autosave_new_post';
        
        const dataToSave = {
            title: title,
            content: content,
            timestamp: new Date().toISOString(),
            category: categorySelect?.value || '',
            tags: tagsInput?.value || ''
        };
        
        localStorage.setItem(storageKey, JSON.stringify(dataToSave));
        lastSavedContent = content;
    }
    
    // 마지막 저장 시간 업데이트
    function updateLastSavedTime() {
        const statusElement = document.getElementById('auto-save-status');
        if (statusElement) {
            const now = new Date();
            const formattedTime = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
            
            statusElement.innerHTML = `<span>마지막 저장: ${formattedTime}</span>`;
            statusElement.classList.add('saved');
            
            // 저장 알림 효과 추가
            setTimeout(() => {
                statusElement.classList.remove('saved');
            }, 2000);
        }
    }
    
    // 자동 저장된 콘텐츠 불러오기 함수
    function loadAutoSavedContent() {
        if (!editorContainer) return;
        
        const postId = editorContainer.dataset.postId;
        const storageKey = postId ? `autosave_post_${postId}` : 'autosave_new_post';
        const savedData = localStorage.getItem(storageKey);
        
        if (savedData) {
            try {
                const parsedData = JSON.parse(savedData);
                const timestamp = new Date(parsedData.timestamp);
                const now = new Date();
                const hoursDiff = (now - timestamp) / (1000 * 60 * 60);
                
                // 24시간 이내의 데이터만 복원 제안
                if (hoursDiff < 24) {
                    const confirmRestore = confirm(
                        `${timestamp.toLocaleString()}에 자동 저장된 글이 있습니다. 복원하시겠습니까?`
                    );
                    
                    if (confirmRestore) {
                        if (titleInput) titleInput.value = parsedData.title || '';
                        if (categorySelect) categorySelect.value = parsedData.category || '';
                        if (tagsInput) tagsInput.value = parsedData.tags || '';
                        
                        // 에디터 콘텐츠 복원
                        try {
                            const contentObj = JSON.parse(parsedData.content);
                            renderContent(contentObj);
                            lastSavedContent = parsedData.content;
                        } catch (e) {
                            console.error('저장된 콘텐츠 파싱 오류:', e);
                            contentArea.innerHTML = parsedData.content;
                            lastSavedContent = parsedData.content;
                        }
                        
                        updateLastSavedTime();
                    } else {
                        // 복원을 취소한 경우 자동 저장 데이터 삭제
                        localStorage.removeItem(storageKey);
                    }
                } else {
                    // 24시간 이상 지난 데이터는 자동 삭제
                    localStorage.removeItem(storageKey);
                }
            } catch (e) {
                console.error('자동 저장 데이터 로드 오류:', e);
                localStorage.removeItem(storageKey);
            }
        }
    }
    
    // 자동 저장 기능 초기화
    function initAutoSave() {
        // editorContainer가 존재하는지 확인
        if (!editorContainer) {
            console.error('Editor container not found!');
            return;
        }
        
        // 기존 자동 저장 데이터 불러오기
        loadAutoSavedContent();
        
        // 자동 저장 인터벌 설정
        autoSaveInterval = setInterval(() => {
            if (!contentArea || !titleInput) return; // 필요한 요소가 없으면 저장하지 않음
            
            const currentContent = JSON.stringify(getContentObject());
            const postTitle = titleInput.value;
            
            // 내용이 있고 마지막 저장 내용과 다른 경우에만 저장
            if (currentContent && currentContent !== lastSavedContent && postTitle) {
                saveContentToLocalStorage(postTitle, currentContent);
                updateLastSavedTime();
            }
        }, AUTO_SAVE_DELAY);
        
        // 자동 저장 상태표시 요소 생성
        const autoSaveStatus = document.createElement('div');
        autoSaveStatus.id = 'auto-save-status';
        autoSaveStatus.className = 'auto-save-status';
        autoSaveStatus.innerHTML = '<span>마지막 저장: 없음</span>';
        autoSaveStatus.setAttribute('aria-live', 'polite'); // 접근성 추가

        try {
            // editorContainer 내부의 .editor-actions 요소 찾기
            const editorActions = editorContainer.querySelector('.editor-actions');

            if (editorActions) {
                // 찾았으면 그 요소 앞에 삽입
                editorContainer.insertBefore(autoSaveStatus, editorActions);
            } else {
                // 못 찾았으면 컨테이너 끝에 추가
                editorContainer.appendChild(autoSaveStatus);
            }
        } catch (e) {
            console.error('자동 저장 상태 표시 요소 추가 오류:', e);
        }
        
        // 페이지 언로드 시 경고 - 개선된 방식
        window.addEventListener('beforeunload', (e) => {
            const currentContent = JSON.stringify(getContentObject());
            const isContentChanged = currentContent !== lastSavedContent && currentContent.trim() !== '{"blocks":[],"time":0,"version":"1.0.0"}';
            
            if (isContentChanged) {
                // 표준 방식으로 경고 메시지 설정
                const message = '저장되지 않은 변경사항이 있습니다. 정말 나가시겠습니까?';
                e.preventDefault(); // 표준
                e.returnValue = message; // IE/Edge 지원
                return message; // 오래된 브라우저 지원
            }
        });
    }
    
    // 콘텐츠 영역 초기화
    if (contentArea) {
        // 편집 가능하게 설정
        contentArea.contentEditable = 'true';
        contentArea.spellcheck = true;
        contentArea.dataset.placeholder = '내용을 입력하세요...';
        contentArea.setAttribute('aria-label', '에디터 콘텐츠 영역'); // 접근성 추가
        
        // 초기 포커스
        contentArea.focus();
        
        // 기존 콘텐츠 로드
        loadExistingContent();
        
        // 자동 저장 초기화
        initAutoSave();
    }
    
    // 이미지 삽입 처리
    function handleImageInsertion() {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.click();
        
        fileInput.addEventListener('change', function() {
            if (fileInput.files && fileInput.files[0]) {
                uploadImage(fileInput.files[0]);
            }
        });
    }
    
    // 이미지 업로드 및 삽입
    function uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        // 진행 표시기
        const progressIndicator = document.createElement('div');
        progressIndicator.className = 'upload-progress';
        progressIndicator.innerHTML = '<span>이미지 업로드 중...</span>';
        progressIndicator.setAttribute('aria-live', 'assertive'); // 접근성 추가
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
                // 이미지 삽입
                const imgHtml = `<img src="${data.file.url}" alt="업로드된 이미지" class="editor-image">`;
                document.execCommand('insertHTML', false, imgHtml);
                
                // 방금 삽입된 이미지에 이벤트 리스너 추가
                setTimeout(() => {
                    const lastImage = contentArea.querySelector('img:last-child');
                    if (lastImage) {
                        // 이미 선택된 이미지 클래스 제거
                        const allImages = contentArea.querySelectorAll('img');
                        allImages.forEach(img => img.classList.remove('selected'));
                        
                        // 새 이미지 선택 표시
                        lastImage.classList.add('selected');
                    }
                }, 100);
            } else {
                alert('이미지 업로드 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            progressIndicator.remove();
            console.error('업로드 오류:', error);
            alert('이미지 업로드 중 오류가 발생했습니다: ' + error.message);
        });
    }
    
    // 링크 삽입 처리 - 임베드 기능 추가
    function handleLinkInsertion() {
        const selection = window.getSelection();
        if (!selection) return;
        
        const selectedText = selection.toString();
        
        // 링크 URL 입력 받기
        const url = prompt('링크 URL을 입력하세요:', 'https://');
        
        if (url && url !== 'https://') {
            // 먼저 미디어 임베드로 처리 시도
            let isMedia = false;
            
            for (const pattern of MEDIA_PATTERNS) {
                if (pattern.regex.test(url)) {
                    const match = url.match(pattern.regex);
                    if (match) {
                        // 선택 영역 삭제
                        if (selection.rangeCount > 0) {
                            const range = selection.getRangeAt(0);
                            range.deleteContents();
                            
                            // 임베드 HTML 삽입
                            const embedHtml = pattern.handler(match);
                            const fragment = document.createDocumentFragment();
                            const div = document.createElement('div');
                            div.innerHTML = embedHtml;
                            
                            while (div.firstChild) {
                                fragment.appendChild(div.firstChild);
                            }
                            
                            range.insertNode(fragment);
                            range.collapse(false);
                        } else {
                            // 선택 영역이 없는 경우 현재 커서 위치에 삽입
                            document.execCommand('insertHTML', false, pattern.handler(match));
                        }
                        
                        isMedia = true;
                        break;
                    }
                }
            }
            
            // 미디어가 아닌 경우 일반 링크로 처리
            if (!isMedia) {
                if (selectedText) {
                    // 선택한 텍스트에 링크 적용
                    document.execCommand('createLink', false, url);
                    
                    // 새 창에서 열리도록 타겟 속성 추가
                    const links = contentArea.querySelectorAll('a[href="' + url + '"]');
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
    }
    
    // 확장된 서식 도구 함수들
    function applyColorStyle() {
        const color = prompt('색상 코드를 입력하세요 (예: #FF0000 또는 red):', '');
        if (color) {
            document.execCommand('foreColor', false, color);
        }
    }
    
    function applyBackgroundColor() {
        const color = prompt('배경색 코드를 입력하세요 (예: #FFFF00 또는 yellow):', '');
        if (color) {
            document.execCommand('hiliteColor', false, color);
        }
    }
    
    function insertTable() {
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
    
    // 이모지 삽입 처리 (스로틀링 적용)
    const throttledInsertEmoji = Utils.throttle(insertEmoji, 300);
    function insertEmoji() {
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
    
    // 코드 블록 삽입
    function insertCodeBlock() {
        const language = prompt('프로그래밍 언어를 입력하세요 (예: javascript, python):', 'javascript');
        
        if (language) {
            const codeBlockHTML = `<pre><code class="language-${language}">여기에 코드를 입력하세요</code></pre>`;
            document.execCommand('insertHTML', false, codeBlockHTML);
            
            // 코드 블록 내부로 커서 이동 및 선택
            const selection = window.getSelection();
            if (!selection) return;
            
            const range = document.createRange();
            const codeElement = contentArea.querySelector('code:last-of-type');
            
            if (codeElement) {
                range.selectNodeContents(codeElement);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }
    }
    
    // URL 붙여넣기 시 자동 임베드 처리
    function processUrl(url) {
        for (const pattern of MEDIA_PATTERNS) {
            if (pattern.regex.test(url)) {
                return pattern.handler(url.match(pattern.regex));
            }
        }
        return null;
    }
    
    // 콘텐츠 영역에 붙여넣기 이벤트 확장
    if (contentArea) {
        contentArea.addEventListener('paste', function(e) {
            e.preventDefault();
            
            // 붙여넣은 텍스트 확인
            const clipboardText = e.clipboardData.getData('text/plain');
            let pasteHTML = e.clipboardData.getData('text/html');
            
            // 미디어 URL인지 확인 및 처리
            if (clipboardText && clipboardText.trim()) {
                const embedHtml = processUrl(clipboardText);
                if (embedHtml) {
                    // 선택 영역 삭제
                    const selection = window.getSelection();
                    if (selection && selection.rangeCount > 0) {
                        const range = selection.getRangeAt(0);
                        range.deleteContents();
                        
                        // 임베드 HTML 삽입
                        const fragment = document.createDocumentFragment();
                        const div = document.createElement('div');
                        div.innerHTML = embedHtml;
                        
                        while (div.firstChild) {
                            fragment.appendChild(div.firstChild);
                        }
                        
                        range.insertNode(fragment);
                        range.collapse(false);
                    } else {
                        document.execCommand('insertHTML', false, embedHtml);
                    }
                    
                    return; // 미디어 URL이 처리되었으므로 기본 붙여넣기 처리 중단
                }
            }
            
            // HTML 붙여넣기 처리
            if (pasteHTML) {
                // HTML 정리 (불필요한 스타일 및 위험 요소 제거)
                const cleanHTML = sanitizeHTML(pasteHTML);
                document.execCommand('insertHTML', false, cleanHTML);
            } else {
                // 텍스트만 있는 경우
                document.execCommand('insertText', false, clipboardText);
            }
        });
    }
    
    // HTML 정리 함수
    function sanitizeHTML(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 스크립트 및 위험한 태그 제거
        const scripts = tempDiv.querySelectorAll('script, iframe, object, embed, style');
        scripts.forEach(node => node.remove());
        
        // 위험한 속성 제거
        const allElements = tempDiv.querySelectorAll('*');
        allElements.forEach(el => {
            const attributes = Array.from(el.attributes);
            attributes.forEach(attr => {
                // on* 이벤트 속성 제거
                if (attr.name.startsWith('on') || 
                    attr.name === 'id' || 
                    attr.name === 'class') {
                    el.removeAttribute(attr.name);
                }
                
                // style 속성은 유지 (에디터 기능 향상을 위해)
            });
        });
        
        return tempDiv.innerHTML;
    }
    
    // 콘텐츠 영역 특수 키 이벤트 처리
    if (contentArea) {
        const throttledKeyHandler = Utils.throttle(handleKeyDown, 100);
        contentArea.addEventListener('keydown', throttledKeyHandler);
    }
    
    function handleKeyDown(e) {
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
            const currentBlock = getParentBlockElement(range.startContainer);
            
            // 코드 블록 내부에서는 기본 동작 유지
            if (isInsideCodeBlock(range.startContainer)) {
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
    
    // 부모 블록 요소 찾기
    function getParentBlockElement(node) {
        while (node && node !== contentArea) {
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
    
    // 코드 블록 내부인지 확인
    function isInsideCodeBlock(node) {
        while (node && node !== contentArea) {
            if (node.nodeName === 'PRE' || node.nodeName === 'CODE') {
                return true;
            }
            node = node.parentNode;
        }
        return false;
    }
    
    // 드래그 앤 드롭으로 이미지 업로드
    if (contentArea) {
        contentArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        contentArea.addEventListener('dragleave', function() {
            this.classList.remove('dragover');
        });
        
        contentArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith('image/')) {
                    uploadImage(file);
                }
            }
        });
    }
    
    // 저장 버튼 이벤트
    if (saveButton) {
        saveButton.addEventListener('click', savePost);
    }
    
    // 제목 입력 검증
    if (titleInput) {
        titleInput.addEventListener('blur', function() {
            validateTitle();
        });
        
        titleInput.addEventListener('input', function() {
            // 입력 시 경고 메시지 제거
            if (this.value.trim()) {
                this.classList.remove('invalid-input');
                titleFeedback.style.display = 'none';
            }
        });
    }
    
    // 제목 유효성 검사
    function validateTitle() {
        if (titleInput && titleFeedback) {
            if (!titleInput.value.trim()) {
                titleInput.classList.add('invalid-input');
                titleFeedback.textContent = '제목을 입력해주세요.';
                titleFeedback.style.display = 'block';
                return false;
            } else {
                titleInput.classList.remove('invalid-input');
                titleFeedback.style.display = 'none';
                return true;
            }
        }
        return true;
    }
    
    // 포스트 저장 함수
    function savePost() {
        if (!titleInput || !contentArea) {
            console.error('필수 에디터 요소가 없습니다.');
            return;
        }
        
        // 제목 유효성 검사
        if (!validateTitle()) {
            titleInput.focus();
            return;
        }
        
        // 내용 유효성 검사
        if (!contentArea.textContent.trim()) {
            contentArea.classList.add('invalid-input');
            contentArea.focus();
            return;
        }
        
        // 콘텐츠 객체 생성
        const contentObj = getContentObject();
        
        const postData = {
            title: titleInput.value.trim(),
            content: JSON.stringify(contentObj),
            category: categorySelect ? categorySelect.value : '',
            tags: tagsInput && tagsInput.value ? tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag) : []
        };
        
        // CSRF 토큰 가져오기
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (!csrfMeta) {
            alert('보안 토큰을 찾을 수 없습니다. 페이지를 새로고침해 주세요.');
            return;
        }
        const csrfToken = csrfMeta.getAttribute('content');
        
        // 포스트 ID 확인 (신규 또는 수정)
        const postId = editorContainer ? editorContainer.dataset.postId : null;
        const url = postId ? `/blog/posts/${postId}` : '/blog/posts';
        const method = postId ? 'PUT' : 'POST';
        
        // 저장 진행 표시기
        const saveIndicator = document.createElement('div');
        saveIndicator.className = 'save-indicator';
        saveIndicator.innerHTML = '<span>저장 중...</span>';
        saveIndicator.setAttribute('aria-live', 'assertive'); // 접근성 추가
        document.body.appendChild(saveIndicator);
        
        // 서버에 저장 요청
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(postData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`서버 응답 오류: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            saveIndicator.remove();
            
            if (data.success) {
                // 자동 저장 데이터 제거
                const storageKey = postId ? `autosave_post_${postId}` : 'autosave_new_post';
                localStorage.removeItem(storageKey);
                
                // 성공 페이지로 이동
                window.location.href = postId ? `/blog/post/${postId}` : `/blog/post/${data.id}`;
            } else {
                alert('저장 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            saveIndicator.remove();
            console.error('저장 오류:', error);
            alert('저장 중 오류가 발생했습니다: ' + error.message);
        });
    }
    
    // 에디터 콘텐츠를 구조화된 객체로 변환
    function getContentObject() {
        if (!contentArea) {
            return { blocks: [], time: new Date().getTime(), version: '1.0.0' };
        }
        
        const blocks = [];
        processContentBlocks(contentArea.childNodes, blocks);
        
        return {
            blocks: blocks,
            time: new Date().getTime(),
            version: '1.0.0'
        };
    }
    
    // 콘텐츠 블록 처리
    function processContentBlocks(nodes, blocks) {
        Array.from(nodes).forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                // 텍스트 노드가 공백이 아니면 단락으로 처리
                if (node.textContent.trim()) {
                    blocks.push({
                        type: 'paragraph',
                        content: node.textContent
                    });
                }
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                processElementNode(node, blocks);
            }
        });
    }
    
    // 요소 노드 처리
    function processElementNode(node, blocks) {
        switch (node.nodeName) {
            case 'P':
                blocks.push({
                    type: 'paragraph',
                    content: node.innerHTML
                });
                break;
                
            case 'H1':
            case 'H2':
            case 'H3':
            case 'H4':
            case 'H5':
            case 'H6':
                blocks.push({
                    type: 'header',
                    level: parseInt(node.nodeName.substring(1)),
                    content: node.innerHTML
                });
                break;
                
            case 'BLOCKQUOTE':
                blocks.push({
                    type: 'quote',
                    content: node.innerHTML
                });
                break;
            
            case 'PRE':
                // 코드 블록 처리
                const codeElement = node.querySelector('code');
                if (codeElement) {
                    const language = codeElement.className.replace('language-', '');
                    blocks.push({
                        type: 'code',
                        content: codeElement.textContent,
                        language: language || 'plaintext'
                    });
                } else {
                    blocks.push({
                        type: 'code',
                        content: node.textContent,
                        language: 'plaintext'
                    });
                }
                break;

            case 'UL':
                blocks.push({
                    type: 'list',
                    style: 'unordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML)
                });
                break;
                
            case 'OL':
                blocks.push({
                    type: 'list',
                    style: 'ordered',
                    items: Array.from(node.querySelectorAll('li')).map(li => li.innerHTML)
                });
                break;
                
            case 'IMG':
                blocks.push({
                    type: 'image',
                    url: node.src,
                    alt: node.alt || '',
                    caption: node.getAttribute('data-caption') || '',
                    width: node.style.width || '',
                    height: node.style.height || ''
                });
                break;
                
            case 'HR':
                blocks.push({
                    type: 'delimiter'
                });
                break;
                
            case 'TABLE':
                const rows = [];
                node.querySelectorAll('tr').forEach(tr => {
                    const cells = Array.from(tr.querySelectorAll('td, th')).map(cell => {
                        return {
                            content: cell.innerHTML,
                            isHeader: cell.nodeName === 'TH'
                        };
                    });
                    rows.push(cells);
                });
                blocks.push({
                    type: 'table',
                    rows: rows
                });
                break;
                
            case 'DIV':
                // 미디어 임베드 처리
                if (node.classList.contains('media-embed')) {
                    const embedType = node.classList.contains('youtube-embed') ? 'youtube' :
                                node.classList.contains('twitch-embed') ? 'twitch' :
                                node.classList.contains('twitter-embed') ? 'twitter' : 'unknown';
                
                    let embedData = {};
                    
                    if (embedType === 'youtube') {
                        const iframe = node.querySelector('iframe');
                        if (iframe) {
                            const src = iframe.src;
                            const videoId = src.match(/embed\/([^?]+)/);
                            if (videoId && videoId[1]) {
                                embedData.videoId = videoId[1];
                            }
                        }
                    } else if (embedType === 'twitter') {
                        embedData.tweetId = node.dataset.tweetId;
                    } else if (embedType === 'twitch') {
                        const iframe = node.querySelector('iframe');
                        if (iframe) {
                            const src = iframe.src;
                            const videoId = src.match(/video=(\d+)/);
                            if (videoId && videoId[1]) {
                                embedData.videoId = videoId[1];
                            }
                        }
                    }
                    
                    blocks.push({
                        type: 'embed',
                        service: embedType,
                        data: embedData,
                        html: node.innerHTML
                    });
                } else if (node.classList.contains('file-preview')) {
                    // 파일 첨부 처리
                    const fileData = {
                        url: node.dataset.fileUrl || '',
                        name: node.dataset.fileName || '',
                        type: node.dataset.fileType || '',
                        size: node.dataset.fileSize || ''
                    };
                    
                    blocks.push({
                        type: 'file',
                        data: fileData
                    });
                } else {
                    // 일반 div는 내부 노드 처리
                    processContentBlocks(node.childNodes, blocks);
                }
                break;
                
            default:
                // 인라인 요소나 기타 요소는 내부 노드 처리
                if (node.childNodes.length > 0) {
                    processContentBlocks(node.childNodes, blocks);
                } else if (node.textContent.trim()) {
                    blocks.push({
                        type: 'paragraph',
                        content: node.outerHTML
                    });
                }
                break;
        }
    }

    // 저장된 콘텐츠 렌더링 함수
    function renderContent(contentObj) {
        if (!contentObj || !contentObj.blocks || !contentArea) {
            return;
        }
        
        let html = '';
        
        contentObj.blocks.forEach(block => {
            switch (block.type) {
                case 'paragraph':
                    html += `<p>${block.content}</p>`;
                    break;
                    
                case 'header':
                    const level = Math.min(Math.max(block.level, 1), 6);
                    html += `<h${level}>${block.content}</h${level}>`;
                    break;
                    
                case 'quote':
                    html += `<blockquote>${block.content}</blockquote>`;
                    break;
                    
                case 'code':
                    const language = block.language || 'plaintext';
                    html += `<pre><code class="language-${language}">${escapeHTML(block.content)}</code></pre>`;
                    break;
                    
                case 'list':
                    const listTag = block.style === 'ordered' ? 'ol' : 'ul';
                    html += `<${listTag}>`;
                    block.items.forEach(item => {
                        html += `<li>${item}</li>`;
                    });
                    html += `</${listTag}>`;
                    break;
                    
                case 'image':
                    html += `<img src="${block.url}" alt="${block.alt || ''}" class="editor-image"`;
                    if (block.width) {
                        html += ` style="width:${block.width}"`;
                    }
                    if (block.height) {
                        html += ` style="height:${block.height}"`;
                    }
                    if (block.caption) {
                        html += ` data-caption="${block.caption}"`;
                    }
                    html += '>';
                    
                    if (block.caption) {
                        html += `<figcaption>${block.caption}</figcaption>`;
                    }
                    break;
                    
                case 'embed':
                    switch (block.service) {
                        case 'youtube':
                            if (block.data && block.data.videoId) {
                                html += `<div class="media-embed youtube-embed">
                                    <iframe width="560" height="315" src="https://www.youtube.com/embed/${block.data.videoId}" 
                                    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; 
                                    gyroscope; picture-in-picture" allowfullscreen></iframe>
                                    <div class="embed-caption">YouTube 동영상</div>
                                </div>`;
                            } else {
                                html += block.html || '';
                            }
                            break;
                            
                        case 'twitter':
                            if (block.data && block.data.tweetId) {
                                html += `<div class="media-embed twitter-embed" data-tweet-id="${block.data.tweetId}">
                                    <blockquote class="twitter-tweet" data-dnt="true">
                                        <a href="https://twitter.com/x/status/${block.data.tweetId}"></a>
                                    </blockquote>
                                    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                                    <div class="embed-caption">Twitter 포스트</div>
                                </div>`;
                            } else {
                                html += block.html || '';
                            }
                            break;
                            
                        default:
                            html += block.html || '';
                            break;
                    }
                    break;
                    
                case 'file':
                    if (block.data && block.data.url) {
                        html += `<div class="file-preview" data-file-url="${block.data.url}" 
                                data-file-name="${block.data.name}" data-file-type="${block.data.type}" 
                                data-file-size="${block.data.size}">
                            <div class="file-icon"><i class="fas fa-file"></i></div>
                            <div class="file-info">
                                <div class="file-name">${block.data.name}</div>
                                <div class="file-meta">${block.data.type}, ${formatFileSize(block.data.size)}</div>
                            </div>
                            <a href="${block.data.url}" class="file-download" target="_blank" 
                            download="${block.data.name}">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>`;
                    }
                    break;
                    
                case 'table':
                    html += '<table class="editor-table"><tbody>';
                    if (block.rows && block.rows.length > 0) {
                        block.rows.forEach(row => {
                            html += '<tr>';
                            if (row && row.length > 0) {
                                row.forEach(cell => {
                                    const cellTag = cell.isHeader ? 'th' : 'td';
                                    html += `<${cellTag}>${cell.content}</${cellTag}>`;
                                });
                            }
                            html += '</tr>';
                        });
                    }
                    html += '</tbody></table>';
                    break;
                    
                case 'delimiter':
                    html += '<hr>';
                    break;
                    
                default:
                    console.warn('지원하지 않는 블록 유형:', block.type);
                    break;
            }
        });
        
        contentArea.innerHTML = html;
        
        // Twitter 위젯 로딩
        if (contentArea.querySelector('.twitter-embed')) {
            if (window.twttr && window.twttr.widgets) {
                window.twttr.widgets.load();
            }
        }
    }

    // 파일 크기 형식화
    function formatFileSize(size) {
        const sizeNum = parseInt(size, 10);
        if (isNaN(sizeNum)) return '';
        
        if (sizeNum < 1024) return sizeNum + ' bytes';
        else if (sizeNum < 1024 * 1024) return (sizeNum / 1024).toFixed(1) + ' KB';
        else if (sizeNum < 1024 * 1024 * 1024) return (sizeNum / (1024 * 1024)).toFixed(1) + ' MB';
        else return (sizeNum / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    }

    // HTML 이스케이프 함수
    function escapeHTML(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    // 이미지 크기 조절 처리
    function resizeSelectedImage() {
        const selectedImage = contentArea.querySelector('img.selected');
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
    }
    
    // 툴바 버튼 이벤트 바인딩
    if (toolbarButtons && toolbarButtons.length > 0) {
        toolbarButtons.forEach(button => {
            const command = button.dataset.command;
            if (!command) return;
            
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                switch(command) {
                    case 'insertImage':
                        handleImageInsertion();
                        break;
                    case 'createLink':
                        handleLinkInsertion();
                        break;
                    case 'foreColor':
                        applyColorStyle();
                        break;
                    case 'hiliteColor':
                        applyBackgroundColor();
                        break;
                    case 'insertTable':
                        insertTable();
                        break;
                    case 'insertEmoji':
                        throttledInsertEmoji();
                        break;
                    case 'insertCodeBlock':
                        insertCodeBlock();
                        break;
                    case 'resizeImage':
                        resizeSelectedImage();
                        break;
                    default:
                        // 기본 명령 실행
                        document.execCommand(command, false, null);
                        break;
                }
                
                // 포커스 되돌리기
                contentArea.focus();
            });
        });
    }
});