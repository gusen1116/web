// autosave.js
class AutoSave {
    constructor(params) {
        // 필요한 요소만 직접 참조 (순환 참조 방지)
        this.contentManager = params.contentManager;
        this.contentArea = params.contentArea;
        this.titleInput = params.titleInput;
        this.categorySelect = params.categorySelect;
        this.tagsInput = params.tagsInput;
        this.editorContainer = params.editorContainer;
        
        // 내부 상태 설정
        this.lastSavedContent = '';
        this.AUTO_SAVE_DELAY = 15000; // 15초
        this.autoSaveInterval = null;
    }
    
    init() {
        // 필수 요소 확인
        if (!this.editorContainer || !this.contentArea || !this.contentManager) {
            console.error('자동 저장에 필요한 요소가 없습니다.');
            return;
        }
        
        // 기존 자동 저장 데이터 불러오기
        this.loadAutoSavedContent();
        
        // 자동 저장 인터벌 설정
        this.startAutoSaveInterval();
        
        // 자동 저장 상태표시 요소 생성
        this.createStatusElement();
        
        // 페이지 언로드 시 처리 (경고창 제거 버전)
        this.setupBeforeUnloadHandler();
    }
    
    startAutoSaveInterval() {
        this.autoSaveInterval = setInterval(() => {
            if (!this.contentArea || !this.titleInput || !this.contentManager) return;
            
            const currentContent = JSON.stringify(this.contentManager.getContentObject());
            const postTitle = this.titleInput.value;
            
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
            this.editorContainer.appendChild(autoSaveStatus);
            
            // 에디터 액션이 있다면 그 위치로 이동
            try {
                const editorActions = this.editorContainer.querySelector('.editor-actions');
                if (editorActions && editorActions.parentNode === this.editorContainer) {
                    this.editorContainer.insertBefore(autoSaveStatus, editorActions);
                } else {
                    // editorActions가 없거나 다른 부모를 가질 경우 그냥 끝에 추가
                    this.editorContainer.appendChild(autoSaveStatus);
                }
            } catch (e) {
                console.error('자동 저장 상태 표시 요소 추가 오류:', e);
                // 오류가 발생해도 기능을 계속하기 위해 그냥 끝에 추가
                try {
                    this.editorContainer.appendChild(autoSaveStatus);
                } catch (e2) {
                    console.error('대체 방법도 실패:', e2);
                }
            }
        } catch (e) {
            console.error('자동 저장 상태 표시 요소 추가 오류:', e);
        }
    }
    
    // 페이지 이탈 시 경고창 제거 버전
    setupBeforeUnloadHandler() {
        window.addEventListener('beforeunload', (e) => {
            if (!this.contentManager) return;
            
            const currentContent = JSON.stringify(this.contentManager.getContentObject());
            if (currentContent !== this.lastSavedContent && currentContent.trim() !== '') {
                // 경고창 대신 자동 저장만 수행
                const postTitle = this.titleInput?.value || '';
                if (postTitle) {
                    this.saveContentToLocalStorage(postTitle, currentContent);
                    this.updateLastSavedTime();
                }
                
                // 경고창 표시 코드 제거 - 여기서 e.preventDefault() 및 returnValue 설정 없음
            }
        });
    }
    
    loadAutoSavedContent() {
        if (!this.editorContainer) return;
        
        const postId = this.editorContainer.dataset.postId;
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
                        if (this.titleInput) this.titleInput.value = parsedData.title || '';
                        if (this.categorySelect) this.categorySelect.value = parsedData.category || '';
                        if (this.tagsInput) this.tagsInput.value = parsedData.tags || '';
                        
                        // 에디터 콘텐츠 복원
                        try {
                            const contentObj = JSON.parse(parsedData.content);
                            this.contentManager.renderContent(contentObj);
                            this.lastSavedContent = parsedData.content;
                        } catch (e) {
                            console.error('저장된 콘텐츠 파싱 오류:', e);
                            if (this.contentArea) {
                                this.contentArea.innerHTML = parsedData.content;
                                this.lastSavedContent = parsedData.content;
                            }
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
        if (!this.editorContainer) return;
        
        const postId = this.editorContainer.dataset.postId;
        const storageKey = postId ? `autosave_post_${postId}` : 'autosave_new_post';
        
        const dataToSave = {
            title: title,
            content: content,
            timestamp: new Date().toISOString(),
            category: this.categorySelect?.value || '',
            tags: this.tagsInput?.value || ''
        };
        
        try {
            localStorage.setItem(storageKey, JSON.stringify(dataToSave));
            this.lastSavedContent = content;
        } catch (e) {
            console.error('로컬 스토리지 저장 오류:', e);
        }
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