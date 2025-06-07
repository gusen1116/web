// main.js - GitHub 스타일 최적화된 JavaScript (최종 수정본)
(function() {
    'use strict';

    // ===== 유틸리티 함수 =====
    const $ = (selector, context = document) => context.querySelector(selector);
    const $$ = (selector, context = document) => context.querySelectorAll(selector);
    
    // ===== 테마 관리 시스템 (3단 토글) =====
    class ThemeManager {
        constructor() {
            this.themes = ['light', 'dark', '8bit'];
            this.currentThemeIndex = 0;
            this.init();
        }

        init() {
            const savedTheme = localStorage.getItem('theme');
            const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

            let initialTheme = 'light';
            if (savedTheme && this.themes.includes(savedTheme)) {
                initialTheme = savedTheme;
            } else if (systemPrefersDark) {
                initialTheme = 'dark';
            }
            
            this.currentThemeIndex = this.themes.indexOf(initialTheme);
            this.applyTheme(initialTheme, true); // 초기 로드 시에는 전환 효과 없음

            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                if (!localStorage.getItem('theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.currentThemeIndex = this.themes.indexOf(newTheme);
                    this.applyTheme(newTheme);
                }
            });
        }

        applyTheme(themeName, isInitialLoad = false) {
            document.documentElement.classList.remove('theme-light', 'theme-dark', 'theme-8bit');
            document.body.classList.remove('theme-light', 'theme-dark', 'theme-8bit', 'dark-theme');
            
            if (themeName !== 'light') {
                document.documentElement.classList.add('theme-' + themeName);
                document.body.classList.add('theme-' + themeName);
                if (themeName === 'dark') {
                    document.body.classList.add('dark-theme'); // 기존 CSS 호환성
                }
            }

            if (!isInitialLoad) {
                document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
                setTimeout(() => {
                    document.body.style.transition = '';
                }, 300);
            }
        }

        toggle() {
            this.currentThemeIndex = (this.currentThemeIndex + 1) % this.themes.length;
            const newTheme = this.themes[this.currentThemeIndex];
            
            localStorage.setItem('theme', newTheme);
            this.applyTheme(newTheme);
        }
    }

    // ===== 모바일 네비게이션 시스템 =====
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


    // ===== 초기화 =====
    document.addEventListener('DOMContentLoaded', () => {
        const themeManager = new ThemeManager();
        new MobileNavigation();

        const themeToggle = $('#themeToggle');
        
        if(themeToggle) themeToggle.addEventListener('click', () => themeManager.toggle());

        // 서비스 워커 등록 코드는 404 오류로 인해 제거되었습니다.
    });

})();