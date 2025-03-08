// Utils.js - 수정 버전
class Utils {
    /**
     * HTML 특수 문자를 이스케이프합니다.
     */
    static escapeHTML(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
    
    /**
     * 파일 크기를 사람이 읽기 쉬운 형식으로 변환합니다.
     */
    static formatFileSize(size) {
        const sizeNum = parseInt(size, 10);
        if (isNaN(sizeNum)) return '';
        
        if (sizeNum < 1024) return sizeNum + ' bytes';
        else if (sizeNum < 1024 * 1024) return (sizeNum / 1024).toFixed(1) + ' KB';
        else if (sizeNum < 1024 * 1024 * 1024) return (sizeNum / (1024 * 1024)).toFixed(1) + ' MB';
        else return (sizeNum / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
    }
    
    /**
     * 함수 호출 빈도를 제한하는 스로틀 함수입니다.
     */
    static throttle(func, delay) {
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
    
    /**
     * HTML을 정제하되 스타일 속성은 유지합니다.
     */
    static sanitizeHTML(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 스크립트 및 위험한 태그 제거
        const scripts = tempDiv.querySelectorAll('script, iframe, object, embed');
        scripts.forEach(node => node.remove());
        
        // 위험한 속성만 제거하고 스타일은 유지
        const allElements = tempDiv.querySelectorAll('*');
        allElements.forEach(el => {
            const attributes = Array.from(el.attributes);
            attributes.forEach(attr => {
                // on* 이벤트 속성만 제거 (스타일 및 클래스 유지)
                if (attr.name.startsWith('on')) {
                    el.removeAttribute(attr.name);
                }
            });
        });
        
        return tempDiv.innerHTML;
    }
    
    /**
     * CSV 파일을 파싱하는 함수
     */
    static parseCSV(csvText) {
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
    
    /**
     * 디버그 로그 함수
     */
    static debug(message, data) {
        if (window.DEBUG_MODE) {
            console.log(`[Editor Debug] ${message}`, data || '');
        }
    }
}

export default Utils;