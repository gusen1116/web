// main.js - 통합 테마 토글 시스템 및 이미지 최적화
(function() {
    'use strict';

    // DOM 요소 선택 헬퍼 함수
    const $ = (selector, context = document) => context.querySelector(selector);

    // 관리할 모든 테마 정보 (라이트, 다크, 픽셀 퓨전)
    const THEMES = [
        { name: 'light', className: '', displayName: '라이트' },
        { name: 'dark', className: ['dark-theme', 'theme-dark'], displayName: '다크' },
        { name: 'pixel-fusion', className: 'theme-pixel-fusion', displayName: '픽셀 퓨전' }
    ];

    // 모든 테마 클래스 이름 목록 (초기화용)
    const ALL_THEME_CLASSES = THEMES.flatMap(theme =>
        Array.isArray(theme.className) ? theme.className : [theme.className]
    ).filter(Boolean);

    /**
     * 이미지 최적화 관리 클래스
     */
    class ImageOptimizer {
        constructor() {
            this.observer = null;
            this.processedImages = new WeakSet();
            this.init();
        }

        init() {
            this.optimizeExistingImages();
            this.setupIntersectionObserver();
            this.setupMutationObserver();
        }

        optimizeExistingImages() {
            const images = document.querySelectorAll('img');
            images.forEach(img => this.optimizeImage(img));
        }

        optimizeImage(img) {
            if (this.processedImages.has(img)) return;
            if (!img.hasAttribute('loading')) img.setAttribute('loading', 'lazy');
            if (!img.hasAttribute('decoding')) img.setAttribute('decoding', 'async');
            this.setupImageLoadingStates(img);
            this.processedImages.add(img);
        }

        setupImageLoadingStates(img) {
            img.classList.add('lazy-image');
            const handleLoad = () => {
                img.classList.add('loaded');
                img.removeEventListener('load', handleLoad);
                img.removeEventListener('error', handleError);
            };
            const handleError = () => {
                img.classList.add('error');
                console.warn('이미지 로딩 실패:', img.src);
                img.removeEventListener('load', handleLoad);
                img.removeEventListener('error', handleError);
            };
            if (img.complete && img.naturalHeight !== 0) {
                handleLoad();
            } else {
                img.addEventListener('load', handleLoad, { passive: true });
                img.addEventListener('error', handleError, { passive: true });
            }
        }

        setupIntersectionObserver() {
            if (!('IntersectionObserver' in window)) return;
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        this.observer.unobserve(img);
                    }
                });
            }, { rootMargin: '50px', threshold: 0.1 });
            document.querySelectorAll('img[data-src]').forEach(img => this.observer.observe(img));
        }

        setupMutationObserver() {
            const mutationObserver = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            if (node.tagName === 'IMG') {
                                this.optimizeImage(node);
                                if (node.dataset.src && this.observer) this.observer.observe(node);
                            }
                            node.querySelectorAll('img').forEach(img => {
                                this.optimizeImage(img);
                                if (img.dataset.src && this.observer) this.observer.observe(img);
                            });
                        }
                    });
                });
            });
            mutationObserver.observe(document.body, { childList: true, subtree: true });
        }

        destroy() {
            if (this.observer) {
                this.observer.disconnect();
                this.observer = null;
            }
        }
    }

    /**
     * 성능 최적화 관리 클래스
     */
    class PerformanceOptimizer {
        constructor() {
            this.animationElements = new WeakSet();
            this.init();
        }

        init() {
            this.optimizeAnimations();
            this.optimizeScrolling();
            this.optimizeFonts();
        }

        optimizeAnimations() {
            const elementsWithTransitions = document.querySelectorAll('[class*="transition"], [class*="hover"], .card, .btn, .post-card');
            elementsWithTransitions.forEach(element => {
                if (this.animationElements.has(element)) return;
                const startAnimation = () => { element.style.willChange = 'transform, opacity'; };
                const endAnimation = () => { element.style.willChange = 'auto'; };
                const transitionEnd = () => { element.style.willChange = 'auto'; };
                element.addEventListener('mouseenter', startAnimation, { passive: true });
                element.addEventListener('focusin', startAnimation, { passive: true });
                element.addEventListener('mouseleave', endAnimation, { passive: true });
                element.addEventListener('focusout', endAnimation, { passive: true });
                element.addEventListener('transitionend', transitionEnd, { passive: true });
                this.animationElements.add(element);
            });
        }

        optimizeScrolling() {
            let ticking = false;
            const updateScrollElements = () => {
                document.querySelectorAll('.fade-in:not(.animation-complete)').forEach(element => {
                    const rect = element.getBoundingClientRect();
                    if (rect.top < window.innerHeight && rect.bottom > 0) {
                        element.classList.add('animation-complete');
                        setTimeout(() => element.style.willChange = 'auto', 500);
                    }
                });
                ticking = false;
            };
            const requestTick = () => { if (!ticking) { requestAnimationFrame(updateScrollElements); ticking = true; } };
            window.addEventListener('scroll', requestTick, { passive: true });
            window.addEventListener('resize', requestTick, { passive: true });
            requestTick();
        }

        optimizeFonts() {
            if ('fonts' in document) {
                document.fonts.ready.then(() => {
                    document.body.classList.add('fonts-loaded');
                    document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div').forEach(el => {
                        el.style.fontDisplay = 'swap';
                    });
                });
            }
        }
    }

    /**
     * 테마 관리 클래스
     */
    class ThemeController {
        constructor(localStorageKey) {
            this.localStorageKey = localStorageKey;
            this.currentThemeIndex = 0;
            this.init();
        }

        init() {
            const saved = localStorage.getItem(this.localStorageKey);
            const idx = THEMES.findIndex(t => t.name === saved);
            if (idx !== -1) this.currentThemeIndex = idx;
            this.applyTheme(this.currentThemeIndex);
        }

        applyTheme(index) {
            const html = document.documentElement;
            const theme = THEMES[index];
            html.classList.remove(...ALL_THEME_CLASSES);
            if (theme.className) {
                const classes = Array.isArray(theme.className) ? theme.className : [theme.className];
                html.classList.add(...classes);
            }
            localStorage.setItem(this.localStorageKey, theme.name);
            document.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
        }

        toggle() {
            this.currentThemeIndex = (this.currentThemeIndex + 1) % THEMES.length;
            this.applyTheme(this.currentThemeIndex);
        }

        getCurrentTheme() {
            return THEMES[this.currentThemeIndex];
        }
    }

    /**
     * 모바일 내비게이션 클래스 (성능 최적화)
     */
    class MobileNavigation {
        constructor() {
            this.isOpen = false;
            this.toggleBtn = $('#mobileToggle');
            this.nav = $('#mobileNav');
            this.closeBtn = $('#mobileNavClose');
            this.overlay = $('#mobileOverlay');
            this.isAnimating = false;
            this._focusHandler = null;
        }

        init() {
            if (!this.toggleBtn || !this.nav) return;
            this.toggleBtn.setAttribute('aria-expanded', 'false');
            this.nav.setAttribute('aria-hidden', 'true');
            this.toggleBtn.addEventListener('click', this.handleToggleClick.bind(this), { passive: false });
            if (this.closeBtn) this.closeBtn.addEventListener('click', this.handleCloseClick.bind(this), { passive: false });
            if (this.overlay) this.overlay.addEventListener('click', this.handleOverlayClick.bind(this), { passive: false });
            document.addEventListener('keydown', this.handleKeydown.bind(this), { passive: false });
            window.addEventListener('resize', this.handleResize.bind(this), { passive: true });

            // 메뉴 링크 클릭 시 자동 닫힘
            const links = this.nav.querySelectorAll('.mobile-nav-link');
            links.forEach(link => link.addEventListener('click', () => this.closeMenu(), { passive: true }));
        }

        handleToggleClick(e) {
            e.preventDefault();
            this.toggleMenu();
        }

        handleCloseClick(e) {
            e.preventDefault();
            this.closeMenu();
        }

        handleOverlayClick(e) {
            e.preventDefault();
            this.closeMenu();
        }

        handleKeydown(e) {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeMenu();
            }
        }

        handleResize() {
            if (window.innerWidth > 768 && this.isOpen) {
                this.closeMenu();
            }
        }

        toggleMenu() {
            if (this.isAnimating) return;
            this.isOpen ? this.closeMenu() : this.openMenu();
        }

        openMenu() {
            if (this.isOpen || this.isAnimating) return;
            this.isAnimating = true;
            this.isOpen = true;
            this.nav.style.willChange = 'transform';
            if (this.overlay) this.overlay.style.willChange = 'opacity';
            document.body.classList.add('nav-open');
            this.nav.classList.add('active');
            this.toggleBtn.classList.add('active');
            this.toggleBtn.setAttribute('aria-expanded', 'true');
            this.nav.setAttribute('aria-hidden', 'false');
            if (this.overlay) this.overlay.classList.add('active');
            setTimeout(() => {
                this.nav.style.willChange = 'auto';
                if (this.overlay) this.overlay.style.willChange = 'auto';
                this.isAnimating = false;
            }, 400);
            this.trapFocus();
        }

        closeMenu() {
            if (!this.isOpen || this.isAnimating) return;
            this.isAnimating = true;
            this.isOpen = false;
            this.nav.style.willChange = 'transform';
            if (this.overlay) this.overlay.style.willChange = 'opacity';
            document.body.classList.remove('nav-open');
            this.nav.classList.remove('active');
            this.toggleBtn.classList.remove('active');
            this.toggleBtn.setAttribute('aria-expanded', 'false');
            this.nav.setAttribute('aria-hidden', 'true');
            if (this.overlay) this.overlay.classList.remove('active');
            setTimeout(() => {
                this.nav.style.willChange = 'auto';
                if (this.overlay) this.overlay.style.willChange = 'auto';
                this.isAnimating = false;
            }, 400);
            if (this._focusHandler) {
                document.removeEventListener('keydown', this._focusHandler);
                this._focusHandler = null;
            }
            this.toggleBtn.focus();
        }

        trapFocus() {
            const focusableElements = this.nav.querySelectorAll(
                'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            this._focusHandler = (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey && document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    } else if (!e.shiftKey && document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            };
            document.addEventListener('keydown', this._focusHandler);
        }
    }

    // 인스턴스 생성 및 초기화
    new ThemeController('themeKey');
    new ImageOptimizer();
    new PerformanceOptimizer();
    const mobileNav = new MobileNavigation();
    mobileNav.init();
})();
