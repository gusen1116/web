// AutoSave.js

class AutoSave {
    constructor(editor) {
        this.editor = editor;
        this.lastSavedContent = '';
        this.AUTO_SAVE_DELAY = 15000; // 15초
        this.autoSaveInterval = null;
    }
    
    init() {
        // editorContainer가 존재하는지 확인
        if (!this.editor.editorContainer) {
            console.error('Editor container not found!');
            return;
        }
        
        // 기존 자동 저장 데이터 불러오기
        this.loadAutoSavedContent();
        
        // 자동 저장 인터벌 설정
        this.startAutoSaveInterval();
        
        // 자동 저장 상태표시 요소 생성
        this.createStatusElement();
        
        // 페이지 언로드 시 경고
        this.setupBeforeUnloadWarning();
    }
    
    startAutoSaveInterval() {
        this.autoSaveInterval = setInterval(() => {
            if (!this.editor.contentArea || !this.editor.titleInput) return;
            
            const currentContent = JSON.stringify(this.editor.contentManager.getContentObject());
            const postTitle = this.editor.titleInput.value;
            
            // 내용이 있고 마지막 저장 내용과 다른 경우에만 저장
            if (currentContent && currentContent !== this.lastSavedContent && postTitle) {
                this.saveContentToLocalStorage(postTitle, currentContent);
                this.updateLastSavedTime();
            }
        }, this.AUTO_SAVE_DELAY);
    }
    
    createStatusElement() {
        const autoSaveStatus = document.createElement('div');
        autoSaveStatus.id = 'auto-save-status';
        autoSaveStatus.className = 'auto-save-status';
        autoSaveStatus.innerHTML = '<span>마지막 저장: 없음</span>';
        autoSaveStatus.setAttribute('aria-live', 'polite');

        try {
            // 안전한 방식으로 상태 요소 추가
            this.editor.editorContainer.appendChild(autoSaveStatus);
            
            // 에디터 액션이 있다면 그 위치로 이동
            try {
                const editorActions = this.editor.editorContainer.querySelector('.editor-actions');
                if (editorActions && editorActions.parentNode === this.editor.editorContainer) {
                    this.editor.editorContainer.insertBefore(autoSaveStatus, editorActions);
                } else {
                    // editorActions가 없거나 다른 부모를 가질 경우 그냥 끝에 추가
                    this.editor.editorContainer.appendChild(autoSaveStatus);
                }
            } catch (e) {
                console.error('자동 저장 상태 표시 요소 추가 오류:', e);
                // 오류가 발생해도 기능을 계속하기 위해 그냥 끝에 추가
                try {
                    this.editor.editorContainer.appendChild(autoSaveStatus);
                } catch (e2) {
                    console.error('대체 방법도 실패:', e2);
                }
            }
        } catch (e) {
            console.error('자동 저장 상태 표시 요소 추가 오류:', e);
        }
    }
    
    setupBeforeUnloadWarning() {
        window.addEventListener('beforeunload', (e) => {
            const currentContent = JSON.stringify(this.editor.contentManager.getContentObject());
            if (currentContent !== this.lastSavedContent && currentContent.trim() !== '') {
                e.preventDefault();
                const message = '저장되지 않은 변경사항이 있습니다. 정말 나가시겠습니까?';
                e.returnValue = message;
                return message;
            }
        });
    }
    
    loadAutoSavedContent() {
        if (!this.editor.editorContainer) return;
        
        const postId = this.editor.editorContainer.dataset.postId;
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
                        if (this.editor.titleInput) this.editor.titleInput.value = parsedData.title || '';
                        if (this.editor.categorySelect) this.editor.categorySelect.value = parsedData.category || '';
                        if (this.editor.tagsInput) this.editor.tagsInput.value = parsedData.tags || '';
                        
                        // 에디터 콘텐츠 복원
                        try {
                            const contentObj = JSON.parse(parsedData.content);
                            this.editor.contentManager.renderContent(contentObj);
                            this.lastSavedContent = parsedData.content;
                        } catch (e) {
                            console.error('저장된 콘텐츠 파싱 오류:', e);
                            this.editor.contentArea.innerHTML = parsedData.content;
                            this.lastSavedContent = parsedData.content;
                        }
                        
                        this.updateLastSavedTime();
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
    
    saveContentToLocalStorage(title, content) {
        if (!this.editor.editorContainer) return;
        
        const postId = this.editor.editorContainer.dataset.postId;
        const storageKey = postId ? `autosave_post_${postId}` : 'autosave_new_post';
        
        const dataToSave = {
            title: title,
            content: content,
            timestamp: new Date().toISOString(),
            category: this.editor.categorySelect?.value || '',
            tags: this.editor.tagsInput?.value || ''
        };
        
        localStorage.setItem(storageKey, JSON.stringify(dataToSave));
        this.lastSavedContent = content;
    }
    
    updateLastSavedTime() {
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
}

export default AutoSave;