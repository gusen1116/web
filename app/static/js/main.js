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
            // 초기 테마 적용은 base.html의 인라인 스크립트가 처리하므로 여기서는 호출하지 않음
            // this.applyTheme(initialTheme, true);

            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                // 사용자가 직접 테마를 설정하지 않았을 경우에만 시스템 설정을 따름
                if (!localStorage.getItem('theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.currentThemeIndex = this.themes.indexOf(newTheme);
                    this.applyTheme(newTheme);
                }
            });
        }

        // ===== 수정된 부분: 테마 클래스를 <html>에만 적용하도록 통일 =====
        applyTheme(themeName) {
            const html = document.documentElement;
            // 모든 테마 관련 클래스 제거
            html.classList.remove('theme-dark', 'dark-theme', 'theme-8bit');

            // 새로운 테마 클래스 추가
            if (themeName === 'dark') {
                html.classList.add('theme-dark', 'dark-theme');
            } else if (themeName === '8bit') {
                html.classList.add('theme-8bit');
            }
            // 'light'는 클래스가 없는 기본 상태

            // 테마 변경 시 부드러운 전환 효과
            document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
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
        const mobileNav = new MobileNavigation();
        mobileNav.init();

        const themeToggle = $('#themeToggle');
        
        if(themeToggle) themeToggle.addEventListener('click', () => themeManager.toggle());

    });

})();