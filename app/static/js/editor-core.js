// editor-core.js
import ContentManager from './content-manager.js';
import ToolbarManager from './toolbar-manager.js';
import AutoSave from './autosave.js';
import MediaHandler from './media-handler.js';
import Utils from './utils.js';
import CodeHighlighter from './code-highlighter.js';
import EmbedHandler from './embed-handler.js';

class EditorCore {
    constructor() {
        // DOM 요소 참조
        this.contentArea = document.getElementById('content-area');
        this.titleInput = document.getElementById('post-title');
        this.categorySelect = document.getElementById('post-category');
        this.tagsInput = document.getElementById('post-tags');
        this.saveButton = document.getElementById('save-post');
        this.editorContainer = document.getElementById('editor-container');
        
        // 필수 요소 검증
        if (!this.contentArea || !this.editorContainer) {
            console.error('필수 에디터 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 모듈 초기화 순서 변경 - MediaHandler를 먼저 생성
        this.mediaHandler = new MediaHandler(this.contentArea);
        this.contentManager = new ContentManager(this.contentArea);
        // MediaHandler를 ToolbarManager에 전달
        this.toolbar = new ToolbarManager(this.contentArea, this.mediaHandler);
        this.embedHandler = new EmbedHandler(this.contentArea);
        this.codeHighlighter = new CodeHighlighter();
        
        // AutoSave는 별도 메서드에서 초기화
        this.autoSave = null;
        
        // 기본 초기화 수행
        this.init();
    }
    
    init() {
        if (!this.contentArea) {
            return;
        }
        
        // 콘텐츠 영역 초기화
        this.contentArea.contentEditable = 'true';
        this.contentArea.spellcheck = true;
        this.contentArea.dataset.placeholder = '내용을 입력하세요...';
        this.contentArea.setAttribute('aria-label', '에디터 콘텐츠 영역');
        
        // 초기 포커스
        this.contentArea.focus();
        
        // 기존 콘텐츠 로드
        if (this.contentManager) {
            this.contentManager.loadExistingContent();
        }
        
        // 에디터 UI 강화
        this.enhanceEditorUI();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
        
        // 코드 하이라이팅 적용
        setTimeout(() => {
            this.applyCodeHighlighting();
        }, 500);
        
        // AutoSave 초기화 (마지막 단계)
        this.initAutoSave();
    }
    
    // 에디터 UI 강화 메서드
    enhanceEditorUI() {
        // 제목 입력 UI 강화
        this.enhanceTitleInput();
        
        // 툴바 UI 개선
        this.enhanceToolbar();
        
        // 에디터 컨테이너에 클래스 추가
        if (this.editorContainer) {
            this.editorContainer.classList.add('enhanced-editor');
        }
        
        // 에디터 영역 크기 조정
        this.adjustEditorSize();
        
        // editor-components.css가 적용되었는지 확인
        this.ensureStylesheetLoaded();
    }
    
    // 제목 입력 UI 강화
    enhanceTitleInput() {
        if (!this.titleInput) return;
        
        // 제목 입력 스타일 강화
        this.titleInput.classList.add('enhanced-title-input');
        
        // 기존 placeholder 제거
        this.titleInput.placeholder = '';
        
        // 제목 입력 필드 강조 애니메이션
        const titleWrapper = document.createElement('div');
        titleWrapper.className = 'title-input-wrapper';
        
        // 제목 라벨 추가
        const titleLabel = document.createElement('label');
        titleLabel.htmlFor = this.titleInput.id || 'post-title';
        titleLabel.className = 'title-label';
        titleLabel.textContent = '제목을 입력하세요';
        
        // DOM 구조 재구성
        if (this.titleInput.parentNode) {
            this.titleInput.parentNode.insertBefore(titleWrapper, this.titleInput);
            titleWrapper.appendChild(titleLabel);
            titleWrapper.appendChild(this.titleInput);
            
            // 초기 상태 확인 및 설정
            if (this.titleInput.value.trim()) {
                titleWrapper.classList.add('has-content');
            }
            
            // 포커스 상태에 따라 강조 효과
            this.titleInput.addEventListener('focus', () => {
                titleWrapper.classList.add('focused');
            });
            
            this.titleInput.addEventListener('blur', () => {
                titleWrapper.classList.remove('focused');
                if (!this.titleInput.value.trim()) {
                    titleWrapper.classList.remove('has-content');
                    // 애니메이션으로 주의 끌기
                    titleWrapper.classList.add('empty', 'attention');
                    setTimeout(() => {
                        titleWrapper.classList.remove('attention');
                    }, 1000);
                } else {
                    titleWrapper.classList.add('has-content');
                    titleWrapper.classList.remove('empty');
                }
            });
            
            // 입력 이벤트 - 입력 중 실시간 업데이트
            this.titleInput.addEventListener('input', () => {
                if (this.titleInput.value.trim()) {
                    titleWrapper.classList.add('has-content');
                    titleWrapper.classList.remove('empty');
                } else {
                    titleWrapper.classList.remove('has-content');
                    titleWrapper.classList.add('empty');
                }
            });
        }
    }
    
    // 툴바 UI 개선
    enhanceToolbar() {
        const toolbar = document.querySelector('.editor-toolbar');
        if (!toolbar) return;
        
        // 툴바에 iframe 삽입 버튼 추가
        const iframeButton = document.createElement('button');
        iframeButton.type = 'button';
        iframeButton.className = 'toolbar-button';
        iframeButton.dataset.command = 'insertIframe';
        iframeButton.title = 'iframe 삽입';
        iframeButton.innerHTML = '<i class="fas fa-window-maximize"></i>';
        
        // 이벤트 리스너 직접 추가 - 문제 수정
        iframeButton.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.embedHandler) {
                this.embedHandler.insertIframe();
            }
        });
        
        // 적절한 위치에 버튼 삽입
        const imageButton = toolbar.querySelector('[data-command="insertImage"]');
        if (imageButton && imageButton.parentNode) {
            imageButton.parentNode.insertBefore(iframeButton, imageButton.nextSibling);
        } else {
            toolbar.appendChild(iframeButton);
        }
    }
    
    // 코드 하이라이팅 적용
    applyCodeHighlighting() {
        if (!this.contentArea || !this.codeHighlighter) return;
        
        // 코드 블록 찾기
        const codeBlocks = this.contentArea.querySelectorAll('pre code');
        
        // 각 코드 블록에 하이라이팅 적용
        codeBlocks.forEach(codeBlock => {
            this.codeHighlighter.highlight(codeBlock);
        });
    }
    
    // 외부 스타일시트가 로드되었는지 확인하는 메서드
    ensureStylesheetLoaded() {
        // editor-components.css가 이미 로드되었는지 확인
        const isStylesheetLoaded = Array.from(document.styleSheets).some(
            sheet => sheet.href && sheet.href.includes('editor-components.css')
        );
        
        // 스타일시트가 로드되지 않았다면 동적으로 추가
        if (!isStylesheetLoaded) {
            console.warn('editor-components.css가 로드되지 않았습니다. 동적으로 추가합니다.');
            const linkElement = document.createElement('link');
            linkElement.rel = 'stylesheet';
            linkElement.href = '/static/css/editor-components.css';
            document.head.appendChild(linkElement);
        }
    }
    
    // 에디터 영역 크기 조정
    adjustEditorSize() {
        if (!this.contentArea) return;
        
        // 에디터 영역 최소 높이 설정
        this.contentArea.style.minHeight = '300px';
        
        // 컨테이너 최대 너비 제한으로 글머리 왼쪽 치우침 방지
        const editorWrapper = this.contentArea.closest('.editor-wrapper') || this.editorContainer;
        if (editorWrapper) {
            editorWrapper.style.maxWidth = '100%';
            editorWrapper.style.boxSizing = 'border-box';
        }
    }
    
    // 페이지 나갈 때 경고창 제거를 위한 AutoSave 수정
    initAutoSave() {
        // AutoSave 매개변수 구성 (순환 참조 없이)
        const autoSaveParams = {
            contentManager: this.contentManager,
            editorContainer: this.editorContainer,
            titleInput: this.titleInput,
            categorySelect: this.categorySelect,
            tagsInput: this.tagsInput,
            contentArea: this.contentArea
        };
        
        // AutoSave 인스턴스 생성 (순환 참조 없음)
        this.autoSave = new AutoSave(autoSaveParams);
        this.autoSave.init();
    }
    
    // 이벤트 리스너 설정 - 페이지 이탈 경고창 제거
    setupEventListeners() {
        // 드래그 앤 드롭 이벤트 설정
        this.setupDragAndDrop();
        
        // 저장 버튼 이벤트 - 경고창 없이 저장
        if (this.saveButton) {
            this.saveButton.addEventListener('click', this.savePostWithoutWarning.bind(this));
        }
        
        // 이미지 선택 이벤트 리스너 추가
        if (this.contentArea) {
            this.contentArea.addEventListener('click', (e) => {
                if (e.target.tagName === 'IMG') {
                    // 이미 선택된 이미지 클래스 제거
                    const allImages = this.contentArea.querySelectorAll('img');
                    allImages.forEach(img => img.classList.remove('selected'));
                    
                    // 클릭한 이미지 선택 표시
                    e.target.classList.add('selected');
                }
            });
        }
    }
    
    // 드래그 앤 드롭으로 이미지 업로드 설정
    setupDragAndDrop() {
        if (!this.contentArea || !this.mediaHandler) return;
        
        // 드래그 오버 처리
        this.contentArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.contentArea.classList.add('dragover');
        });
        
        // 드래그 떠남 처리
        this.contentArea.addEventListener('dragleave', () => {
            this.contentArea.classList.remove('dragover');
        });
        
        // 드롭 처리
        this.contentArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.contentArea.classList.remove('dragover');
            
            // 파일 확인 및 처리
            if (e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith('image/')) {
                    this.mediaHandler.uploadImage(file);
                }
            }
        });
    }
    
    // 경고창 없이 저장하는 메서드
    savePostWithoutWarning() {
        if (!this.titleInput || !this.contentArea) {
            console.error('필수 에디터 요소가 없습니다.');
            return;
        }
        
        // 제목이 비어있는 경우 제목 입력 필드에 주의 환기
        if (!this.titleInput.value.trim()) {
            const titleWrapper = this.titleInput.closest('.title-input-wrapper');
            if (titleWrapper) {
                titleWrapper.classList.add('empty', 'attention');
                setTimeout(() => {
                    titleWrapper.classList.remove('attention');
                }, 1000);
            }
            this.titleInput.focus();
            return;
        }
        
        // 콘텐츠 객체 생성
        const contentObj = this.contentManager.getContentObject();
        
        const postData = {
            title: this.titleInput.value.trim(),
            content: JSON.stringify(contentObj),
            category: this.categorySelect ? this.categorySelect.value : '',
            tags: this.tagsInput && this.tagsInput.value ? 
                this.tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag) : []
        };
        
        // CSRF 토큰 가져오기
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (!csrfMeta) {
            alert('보안 토큰을 찾을 수 없습니다. 페이지를 새로고침해 주세요.');
            return;
        }
        const csrfToken = csrfMeta.getAttribute('content');
        
        // 포스트 ID 확인 (신규 또는 수정)
        const postId = this.editorContainer ? this.editorContainer.dataset.postId : null;
        const url = postId ? `/blog/posts/${postId}` : '/blog/posts';
        const method = postId ? 'PUT' : 'POST';
        
        // 저장 진행 표시기
        const saveIndicator = document.createElement('div');
        saveIndicator.className = 'save-indicator';
        saveIndicator.innerHTML = '<span>저장 중...</span>';
        saveIndicator.setAttribute('aria-live', 'assertive');
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
                
                // 성공 페이지로 이동 - beforeunload 경고 우회
                window.onbeforeunload = null;
                window.location.href = postId ? `/blog/post/${postId}` : `/blog/post/${data.id}`;
            } else {
                alert('저장 실패: ' + (data.message || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            saveIndicator.remove();
            console.error('저장 오류:', error);
            alert('저장 중 오류가 발생했습니다.');
        });
    }
}

export default EditorCore;