// 상단의 정적 import는 제거하고 dynamic import만 사용하거나
// 아래와 같이 정적 import를 유지하는 방식으로 수정합니다.

import EditorCore from './editor-core.js'; 

// 전역 설정
window.DEBUG_MODE = false; // 디버깅 모드 활성화 여부

document.addEventListener('DOMContentLoaded', function() {
    // 이 부분은 디버깅을 위해 추가
    console.log('DOM이 준비되었습니다.');
    
    // 에디터 컨테이너가 있는지 확인
    const editorContainer = document.getElementById('editor-container');
    console.log('에디터 컨테이너:', editorContainer);
    
    if (editorContainer) {
        try {
            // 이미 import된 EditorCore 사용
            window.editor = new EditorCore();
            console.log('에디터 초기화 완료:', window.editor);
        } catch (error) {
            console.error('에디터 초기화 실패:', error);
        }
    }
});