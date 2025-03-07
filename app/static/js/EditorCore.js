// EditorCore.js
import AutoSave from '/AutoSave.js';
import ContentManager from './ContentManager.js';
import ToolbarManager from './ToolbarManager.js';
import MediaHandler from './MediaHandler.js';

class EditorCore {
    constructor() {
        // 핵심 요소 참조
        this.contentArea = document.getElementById('content-area');
        this.titleInput = document.getElementById('post-title');
        this.categorySelect = document.getElementById('post-category');
        this.tagsInput = document.getElementById('post-tags');
        this.saveButton = document.getElementById('save-post');
        this.editorContainer = document.getElementById('editor-container');
        
        // 모듈 초기화
        this.contentManager = new ContentManager(this.contentArea);
        this.autoSave = new AutoSave(this);
        this.toolbar = new ToolbarManager(this);
        this.mediaHandler = new MediaHandler(this);
        
        this.init();
    }
    
    init() {
        if (!this.contentArea) {
            console.error('편집기 콘텐츠 영역을 찾을 수 없습니다.');
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
        this.contentManager.loadExistingContent();
        
        // 자동 저장 초기화
        this.autoSave.init();
        
        // 저장 버튼 이벤트
        if (this.saveButton) {
            this.saveButton.addEventListener('click', this.savePost.bind(this));
        }
        
        // 드래그 앤 드롭 설정
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        if (!this.contentArea) return;
        
        const throttledDragOver = this.mediaHandler.throttle((e) => {
            e.preventDefault();
            this.contentArea.classList.add('dragover');
        }, 100);
        
        this.contentArea.addEventListener('dragover', throttledDragOver);
        
        this.contentArea.addEventListener('dragleave', () => {
            this.contentArea.classList.remove('dragover');
        });
        
        this.contentArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.contentArea.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0];
                if (file.type.startsWith('image/')) {
                    this.mediaHandler.uploadImage(file);
                }
            }
        });
    }
    
    savePost() {
        if (!this.titleInput || !this.contentArea) {
            console.error('필수 에디터 요소가 없습니다.');
            return;
        }
        
        // 기본 유효성 검사
        if (!this.titleInput.value.trim()) {
            alert('제목을 입력해주세요.');
            this.titleInput.focus();
            return;
        }
        
        if (!this.contentArea.textContent.trim()) {
            alert('내용을 입력해주세요.');
            this.contentArea.focus();
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
                
                // 성공 페이지로 이동
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

// 문서가 준비되면 에디터 초기화
document.addEventListener('DOMContentLoaded', function() {
    window.editor = new EditorCore();
});

export default EditorCore;