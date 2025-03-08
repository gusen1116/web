// main.js
// main.js
import EditorCore from './editorcore.js'; // 상대 경로로 수정;

// 전역 설정
window.DEBUG_MODE = false; // 디버깅 모드 활성화 여부

// 문서 로드 완료 시 에디터 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 에디터 존재 여부 확인
    const editorContainer = document.getElementById('editor-container');
    if (editorContainer) {
        window.editor = new EditorCore();
        console.log('Editor initialized successfully.');
    }
});