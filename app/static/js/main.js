// main.js
// 정적 임포트 유지
import EditorCore from '/static/js/editor-core.js';

// 전역 설정
window.DEBUG_MODE = true; // 디버깅 활성화

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM이 준비되었습니다. 에디터 초기화를 시작합니다.');
    
    // 에디터 컨테이너 확인
    const editorContainer = document.getElementById('editor-container');
    console.log('에디터 컨테이너 상태:', editorContainer ? '찾음' : '찾을 수 없음');
    
    if (editorContainer) {
        try {
            // 모듈 의존성 로딩 확인
            console.log('EditorCore 모듈 로딩 상태:', typeof EditorCore);
            
            // 에디터 초기화 시도
            window.editor = new EditorCore();
            console.log('에디터 초기화 완료:', window.editor);
            
        } catch (error) {
            console.error('에디터 초기화 실패:', error);
            
            // 폴백: 기본 contenteditable 기능만 활성화
            try {
                const contentArea = document.getElementById('content-area');
                if (contentArea) {
                    contentArea.contentEditable = 'true';
                    contentArea.spellcheck = true;
                    contentArea.dataset.placeholder = '내용을 입력하세요...';
                    console.log('폴백: 기본 편집 기능만 활성화했습니다.');
                }
            } catch (fallbackError) {
                console.error('폴백 초기화도 실패:', fallbackError);
            }
        }
    } else {
        console.log('현재 페이지에 에디터 컨테이너가 없습니다.');
    }
});