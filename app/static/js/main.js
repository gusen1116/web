// main.js - 통합 테마 토글 시스템
(function() {
    'use strict';

    const $ = (selector, context = document) => context.querySelector(selector);

    // 관리할 모든 테마 정보
    const THEMES = [
        { name: 'light', className: '', displayName: '라이트' },
        { name: 'dark', className: ['dark-theme', 'theme-dark'], displayName: '다크' },
        { name: '8bit', className: 'theme-8bit', displayName: '8비트' },
        { name: 'cyan-orange', className: 'theme-cyan-orange', displayName: '시안 오렌지' },
        { name: 'purple-green', className: 'theme-purple-green', displayName: '퍼플 그린' },
        { name: 'neon-dystopia', className: 'theme-neon-dystopia', displayName: '네온 디스토피아' },
        { name: 'pixel-glitch', className: 'theme-pixel-glitch', displayName: '픽셀 글리치' },
        { name: 'pixel-fusion', className: 'theme-pixel-fusion', displayName: '픽셀 퓨전' } // 신규 테마 추가
    ];
    
    // 모든 테마 클래스 이름 목록 (초기화용)
    const ALL_THEME_CLASSES = THEMES.flatMap(theme => Array.isArray(theme.className) ? theme.className : [theme.className]).filter(Boolean);

    class ThemeController {
        constructor(localStorageKey) {
            this.localStorageKey = localStorageKey;
            this.currentThemeIndex = 0;
            this.themeIndicator = $('#themeIndicator'); // 테마 이름 표시 요소
            this.init();
        }

        init() {
            const savedThemeName = localStorage.getItem(this.localStorageKey);
            const savedThemeIndex = THEMES.findIndex(theme => theme.name === savedThemeName);
            
            if (savedThemeIndex !== -1) {
                this.currentThemeIndex = savedThemeIndex;
            }
            this.applyTheme(this.currentThemeIndex);
        }

        applyTheme(index) {
            const html = document.documentElement;
            const theme = THEMES[index];

            // 1. 모든 테마 클래스 제거
            html.classList.remove(...ALL_THEME_CLASSES);

            // 2. 새 테마 클래스 추가
            if (theme.className) {
                const classesToAdd = Array.isArray(theme.className) ? theme.className : [theme.className];
                html.classList.add(...classesToAdd);
            }
            
            // 3. 로컬 스토리지에 저장
            localStorage.setItem(this.localStorageKey, theme.name);

            // 4. 헤더의 테마 표시기 업데이트
            if (this.themeIndicator) {
                this.themeIndicator.textContent = `테마: ${theme.displayName}`;
                this.themeIndicator.dataset.theme = theme.name; // 데이터 속성으로 현재 테마 이름 저장
            }
        }

        toggle() {
            this.currentThemeIndex = (this.currentThemeIndex + 1) % THEMES.length;
            this.applyTheme(this.currentThemeIndex);
        }
    }

    class MobileNavigation {
        constructor() {
            this.isOpen = false;
            this.toggle = $('#mobileToggle');
            this.nav = $('#mobileNav');
            this.close = $('#mobileNavClose');
            this.overlay = $('#mobileOverlay');
        }
        init() {
            if (!this.toggle || !this.nav) return;
            this.toggle.addEventListener('click', () => this.toggleMenu());
            this.close?.addEventListener('click', () => this.closeMenu());
            this.overlay?.addEventListener('click', () => this.closeMenu());
        }
        toggleMenu() { this.isOpen ? this.closeMenu() : this.openMenu(); }
        openMenu() {
            if(this.isOpen) return;
            this.isOpen = true;
            document.body.classList.add('nav-open');
            this.nav.classList.add('active');
            this.toggle.classList.add('active');
            this.overlay?.classList.add('active');
        }
        closeMenu() {
            if(!this.isOpen) return;
            this.isOpen = false;
            document.body.classList.remove('nav-open');
            this.nav.classList.remove('active');
            this.toggle.classList.remove('active');
            this.overlay?.classList.remove('active');
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        // 모바일 내비게이션 초기화
        const mobileNav = new MobileNavigation();
        mobileNav.init();

        // 통합 테마 컨트롤러 초기화
        const themeController = new ThemeController('wagusen_theme_v2');
        
        // 통합 테마 토글 버튼 이벤트 리스너
        const unifiedThemeToggle = $('#unifiedThemeToggle');
        if (unifiedThemeToggle) {
            unifiedThemeToggle.addEventListener('click', () => themeController.toggle());
        }
    });

})();
