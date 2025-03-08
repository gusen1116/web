// HistoryManager.js
class HistoryManager {
    constructor(options) {
        this.contentArea = options.contentArea;
        this.maxHistoryLength = 50;
        this.history = [];
        this.currentIndex = -1;
        
        this.init();
    }
    
    init() {
        // 초기 상태 저장
        this.saveState();
        
        // 변경 감지 이벤트 설정
        this.setupChangeDetection();
    }
    
    saveState() {
        // 현재 상태 저장
        if (!this.contentArea) return;
        
        // 현재 인덱스 이후의 히스토리 제거
        if (this.currentIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.currentIndex + 1);
        }
        
        // 새 상태 추가
        this.history.push(this.contentArea.innerHTML);
        this.currentIndex = this.history.length - 1;
        
        // 히스토리 크기 제한
        if (this.history.length > this.maxHistoryLength) {
            this.history.shift();
            this.currentIndex--;
        }
        
        // 버튼 상태 업데이트
        this.updateButtonStates();
    }
    
    setupChangeDetection() {
        // 콘텐츠 변경 감지
        if (this.contentArea) {
            this.contentArea.addEventListener('input', () => {
                this.saveState();
            });
        }
    }
    
    undo() {
        // 실행 취소
        if (this.currentIndex <= 0) return;
        
        this.currentIndex--;
        this.contentArea.innerHTML = this.history[this.currentIndex];
        this.updateButtonStates();
    }
    
    redo() {
        // 다시 실행
        if (this.currentIndex >= this.history.length - 1) return;
        
        this.currentIndex++;
        this.contentArea.innerHTML = this.history[this.currentIndex];
        this.updateButtonStates();
    }
    
    updateButtonStates() {
        // 버튼 상태 업데이트
        const undoBtn = document.querySelector('[data-command="undo"]');
        const redoBtn = document.querySelector('[data-command="redo"]');
        
        if (undoBtn) undoBtn.disabled = this.currentIndex <= 0;
        if (redoBtn) redoBtn.disabled = this.currentIndex >= this.history.length - 1;
    }
}

export default HistoryManager;