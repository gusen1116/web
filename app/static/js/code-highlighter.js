// code-highlighter.js
class CodeHighlighter {
    constructor() {
        // Prism.js 또는 Highlight.js와 같은 라이브러리를 동적으로 로드할 수 있음
        this.loaded = false;
        this.loadLibrary();
    }
    
    loadLibrary() {
        // 이미 로드된 경우 중복 로드 방지
        if (window.Prism || document.querySelector('script[src*="prism.js"]')) {
            this.loaded = true;
            return;
        }
        
        // CSS 로드
        const prismCSS = document.createElement('link');
        prismCSS.rel = 'stylesheet';
        prismCSS.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/themes/prism.min.css';
        document.head.appendChild(prismCSS);
        
        // JS 로드
        const prismScript = document.createElement('script');
        prismScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/prism.min.js';
        prismScript.onload = () => {
            // 추가 언어 로드
            this.loadAdditionalLanguages();
            this.loaded = true;
            
            // 로드 완료 후 현재 페이지의 코드 블록 강조
            this.highlightAll();
        };
        document.head.appendChild(prismScript);
    }
    
    loadAdditionalLanguages() {
        // 자주 사용되는 언어 추가 로드
        const languages = [
            'javascript', 'css', 'markup', 'python', 'java', 'csharp', 
            'php', 'ruby', 'go', 'typescript', 'bash', 'sql'
        ];
        
        languages.forEach(lang => {
            if (lang === 'markup' || lang === 'javascript' || lang === 'css') return; // 기본 포함된 언어
            
            const script = document.createElement('script');
            script.src = `https://cdnjs.cloudflare.com/ajax/libs/prism/1.28.0/components/prism-${lang}.min.js`;
            document.head.appendChild(script);
        });
    }
    
    highlight(element) {
        if (!this.loaded) {
            console.warn('구문 강조 라이브러리가 아직 로드되지 않았습니다.');
            return;
        }
        
        if (!element) return;
        
        try {
            window.Prism.highlightElement(element);
        } catch (e) {
            console.error('구문 강조 오류:', e);
        }
    }
    
    highlightAll() {
        if (!this.loaded) {
            console.warn('구문 강조 라이브러리가 아직 로드되지 않았습니다.');
            return;
        }
        
        try {
            window.Prism.highlightAll();
        } catch (e) {
            console.error('전체 구문 강조 오류:', e);
        }
    }
    
    // 코드 블록에 사용할 수 있는 언어 목록 반환
    getAvailableLanguages() {
        if (!this.loaded || !window.Prism || !window.Prism.languages) {
            return ['plaintext', 'javascript', 'css', 'html'];
        }
        
        return Object.keys(window.Prism.languages).filter(lang => 
            typeof window.Prism.languages[lang] === 'object'
        );
    }
}

export default CodeHighlighter;