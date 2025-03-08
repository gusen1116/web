// utils.js
class Utils {
    /**
     * HTML 특수 문자를 이스케이프합니다.
     */
    static escapeHTML(text) {
        if (typeof text !== 'string') return '';
        
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
     * 디바운스 함수 - 연속된 호출 중 마지막 호출만 실행합니다.
     */
    static debounce(func, delay) {
        let timer = null;
        return function(...args) {
            const context = this;
            clearTimeout(timer);
            timer = setTimeout(() => {
                func.apply(context, args);
            }, delay);
        };
    }
    
    /**
     * HTML을 정제하되 스타일 속성은 유지합니다.
     */
    static sanitizeHTML(html) {
        if (typeof html !== 'string') return '';
        
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
        if (typeof csvText !== 'string') return [];
        
        const lines = csvText.split('\n');
        if (lines.length < 1) return [];
        
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
     * 오늘 날짜를 YYYY-MM-DD 형식으로 반환합니다.
     */
    static getTodayDate() {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    /**
     * 브라우저의 로컬 스토리지에 데이터를 안전하게 저장합니다.
     */
    static saveToLocalStorage(key, data) {
        try {
            const serializedData = JSON.stringify(data);
            localStorage.setItem(key, serializedData);
            return true;
        } catch (error) {
            console.error('로컬 스토리지 저장 오류:', error);
            return false;
        }
    }
    
    /**
     * 브라우저의 로컬 스토리지에서 데이터를 안전하게 불러옵니다.
     */
    static loadFromLocalStorage(key, defaultValue = null) {
        try {
            const serializedData = localStorage.getItem(key);
            if (serializedData === null) {
                return defaultValue;
            }
            return JSON.parse(serializedData);
        } catch (error) {
            console.error('로컬 스토리지 로드 오류:', error);
            return defaultValue;
        }
    }
    
    /**
     * 요소의 높이를 자동으로 조정합니다 (textarea 등에 유용).
     */
    static autoResizeElement(element) {
        if (!element) return;
        
        element.style.height = 'auto';
        element.style.height = (element.scrollHeight) + 'px';
    }
    
    /**
     * 디버그 로그 함수
     */
    static debug(message, data) {
        if (window.DEBUG_MODE) {
            console.log(`[Editor Debug] ${message}`, data || '');
        }
    }
    
    /**
     * DOM 요소가 로드될 때까지 대기한 후 콜백을 실행합니다.
     */
    static waitForElement(selector, callback, maxAttempts = 10) {
        let attempts = 0;
        
        const checkElement = () => {
            attempts++;
            const element = document.querySelector(selector);
            
            if (element) {
                callback(element);
                return;
            }
            
            if (attempts >= maxAttempts) {
                console.warn(`요소를 찾을 수 없음: ${selector} (최대 시도 횟수 도달)`);
                return;
            }
            
            setTimeout(checkElement, 300);
        };
        
        checkElement();
    }
}

export default Utils;