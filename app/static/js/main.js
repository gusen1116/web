// main.js - 2개의 독립적인 테마 토글 시스템 관리
(function() {
    'use strict';

    const $ = (selector, context = document) => context.querySelector(selector);
    
    // 관리할 모든 테마 클래스 목록
    const ALL_THEME_CLASSES = ['theme-dark', 'dark-theme', 'theme-8bit', 'theme-royal-cream', 'theme-royal-pixel', 'theme-future-pixel'];
    
    // 테마 상태를 관리하는 범용 클래스
    class ThemeController {
        constructor(themes, localStorageKey, otherController) {
            this.themes = themes;
            this.localStorageKey = localStorageKey;
            this.otherController = otherController;
            this.currentThemeIndex = 0;
            this.init();
        }

        init() {
            const savedTheme = localStorage.getItem(this.localStorageKey);
            if (savedTheme && this.themes.includes(savedTheme)) {
                this.currentThemeIndex = this.themes.indexOf(savedTheme);
            }
        }

        applyTheme(themeName) {
            const html = document.documentElement;
            html.classList.remove(...ALL_THEME_CLASSES);

            const classMap = {
                'dark': ['theme-dark', 'dark-theme'],
                '8bit': ['theme-8bit'],
                'royal-cream': ['theme-royal-cream'],
                'royal-pixel': ['theme-royal-pixel'],
                'future-pixel': ['theme-future-pixel']
            };

            if (classMap[themeName]) {
                html.classList.add(...(Array.isArray(classMap[themeName]) ? classMap[themeName] : [classMap[themeName]]));
            }

            // 'light' 테마는 아무 클래스도 추가하지 않음
            
            if (themeName !== 'light') {
                localStorage.setItem(this.localStorageKey, themeName);
            }
        }

        toggle() {
            // 다른 컨트롤러의 상태를 리셋하고 로컬 스토리지에서 제거
            if (this.otherController) {
                this.otherController.reset();
                localStorage.removeItem(this.otherController.localStorageKey);
            }

            this.currentThemeIndex = (this.currentThemeIndex + 1) % this.themes.length;
            const newTheme = this.themes[this.currentThemeIndex];
            this.applyTheme(newTheme);
        }
        
        reset() {
            this.currentThemeIndex = 0;
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
        const mobileNav = new MobileNavigation();
        mobileNav.init();

        // 두 개의 테마 컨트롤러 생성
        const baseThemes = ['light', 'dark', '8bit'];
        const newThemes = ['light', 'royal-cream', 'royal-pixel', 'future-pixel'];
        
        const baseThemeController = new ThemeController(baseThemes, 'theme');
        const newThemeController = new ThemeController(newThemes, 'new_theme');
        
        // 서로를 참조하도록 설정하여 상호 리셋 기능 구현
        baseThemeController.otherController = newThemeController;
        newThemeController.otherController = baseThemeController;

        const baseThemeToggle = $('#baseThemeToggle');
        const newThemeToggle = $('#newThemeToggle');
        
        if (baseThemeToggle) {
            baseThemeToggle.addEventListener('click', () => baseThemeController.toggle());
        }
        
        if (newThemeToggle) {
            newThemeToggle.addEventListener('click', () => newThemeController.toggle());
        }
    });

})();