// app/static/js/main.js
(function() {
    'use strict';

    const $ = (selector, context = document) => context.querySelector(selector);

    const THEMES = [
        { name: 'light', className: '', displayName: '라이트' },
        { name: 'dark', className: ['dark-theme'], displayName: '다크' },
        { name: '8bit', className: 'theme-cyberbit', displayName: '8비트' }
    ];
    
    const ALL_THEME_CLASSES = THEMES.flatMap(theme =>
        Array.isArray(theme.className) ? theme.className : [theme.className]
    ).filter(Boolean);

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
            document.querySelectorAll('img').forEach(img => this.optimizeImage(img));
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
            const handleLoad = () => { img.classList.add('loaded'); img.removeEventListener('load', handleLoad); img.removeEventListener('error', handleError); };
            const handleError = () => { img.classList.add('error'); console.warn('이미지 로딩 실패:', img.src); img.removeEventListener('load', handleLoad); img.removeEventListener('error', handleError); };
            if (img.complete && img.naturalHeight !== 0) handleLoad();
            else { img.addEventListener('load', handleLoad, { passive: true }); img.addEventListener('error', handleError, { passive: true }); }
        }

        setupIntersectionObserver() {
            if (!('IntersectionObserver' in window)) return;
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
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
    }

    class PerformanceOptimizer {
        constructor() {
            this.init();
        }

        init() {
            this.optimizeAnimations();
            this.optimizeScrolling();
            this.optimizeFonts();
        }

        optimizeAnimations() {
            document.querySelectorAll('[class*="transition"], [class*="hover"], .card, .btn, .post-card').forEach(element => {
                const startAnimation = () => { element.style.willChange = 'transform, opacity'; };
                const endAnimation = () => { element.style.willChange = 'auto'; };
                element.addEventListener('mouseenter', startAnimation, { passive: true });
                element.addEventListener('focusin', startAnimation, { passive: true });
                element.addEventListener('mouseleave', endAnimation, { passive: true });
                element.addEventListener('focusout', endAnimation, { passive: true });
                element.addEventListener('transitionend', () => { element.style.willChange = 'auto'; }, { passive: true });
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
                });
            }
        }
    }

    class ThemeController {
        constructor(localStorageKey) {
            this.localStorageKey = localStorageKey;
            this.toggleButtons = Array.from(document.querySelectorAll('[data-theme-toggle]'));
            this.currentTheme = THEMES[0];
            this.init();
        }

        init() {
            const saved = localStorage.getItem(this.localStorageKey);
            const currentTheme = THEMES.find(t => t.name === saved) || THEMES[0];
            this.applyTheme(currentTheme, { emitEvent: false });
            this.updateToggleState(currentTheme);

            this.toggleButtons.forEach(button => {
                button.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.toggle();
                }, { passive: false });
            });

            document.addEventListener('themeChanged', ({ detail }) => {
                if (!detail) return;
                this.currentTheme = detail;
                this.updateToggleState(detail);
            }, { passive: true });
        }

        applyTheme(theme, options = {}) {
            const { emitEvent = true } = options;
            const html = document.documentElement;
            html.classList.remove(...ALL_THEME_CLASSES);
            
            if (theme.className) {
                const classes = Array.isArray(theme.className) ? theme.className : [theme.className];
                html.classList.add(...classes);
            }
            
            localStorage.setItem(this.localStorageKey, theme.name);
            this.currentTheme = theme;
            if (emitEvent) {
                document.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
            }
            this.updateToggleState(theme);
        }

        updateToggleState(theme) {
            const isAlternateTheme = theme.name !== THEMES[0].name;
            this.toggleButtons.forEach(button => {
                button.setAttribute('aria-pressed', isAlternateTheme ? 'true' : 'false');
                button.classList.toggle('is-active', isAlternateTheme);
                const slider = button.querySelector('[data-theme-slider]');
                if (slider) {
                    slider.classList.toggle('active', isAlternateTheme);
                }
            });
        }

        toggle() {
            const currentIndex = THEMES.findIndex(t => t.name === this.currentTheme.name);
            const nextIndex = (currentIndex + 1) % THEMES.length;
            this.applyTheme(THEMES[nextIndex]);
        }
    }

    class MobileNavigation {
        constructor() {
            this.isOpen = false;
            this.toggleBtn = $('#mobileToggle');
            this.nav = $('#mobileNav');
            this.closeBtn = $('#mobileNavClose');
            this.overlay = $('#mobileOverlay');
            this.isAnimating = false;
            this._focusHandler = null;
            this.scrollPosition = 0;
        }

        init() {
            if (!this.toggleBtn || !this.nav) return;
            this.toggleBtn.setAttribute('aria-expanded', 'false');
            this.nav.setAttribute('aria-hidden', 'true');
            this.toggleBtn.addEventListener('click', (e) => { e.preventDefault(); this.toggleMenu(); }, { passive: false });
            if (this.closeBtn) this.closeBtn.addEventListener('click', (e) => { e.preventDefault(); this.closeMenu(); }, { passive: false });
            if (this.overlay) this.overlay.addEventListener('click', (e) => { e.preventDefault(); this.closeMenu(); }, { passive: false });
            document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && this.isOpen) this.closeMenu(); }, { passive: false });
            window.addEventListener('resize', () => { if (window.innerWidth > 768 && this.isOpen) this.closeMenu(); }, { passive: true });
            this.nav.querySelectorAll('.mobile-nav-link').forEach(link => {
                if (link.hasAttribute('data-theme-toggle')) return;
                link.addEventListener('click', () => this.closeMenu(), { passive: true });
            });
        }

        toggleMenu() {
            if (this.isAnimating) return;
            this.isOpen ? this.closeMenu() : this.openMenu();
        }

        openMenu() {
            if (this.isOpen || this.isAnimating) return;
            this.isAnimating = true;
            this.isOpen = true;
            this.scrollPosition = window.scrollY || document.documentElement.scrollTop || 0;
            document.body.style.top = `-${this.scrollPosition}px`;
            document.body.classList.add('nav-open');
            this.nav.classList.add('active');
            this.toggleBtn.classList.add('active');
            this.toggleBtn.setAttribute('aria-expanded', 'true');
            this.nav.setAttribute('aria-hidden', 'false');
            if (this.overlay) {
                this.overlay.classList.add('active');
                this.overlay.setAttribute('aria-hidden', 'false');
            }
            setTimeout(() => { this.isAnimating = false; }, 400);
            this.trapFocus();
        }

        closeMenu() {
            if (!this.isOpen || this.isAnimating) return;
            this.isAnimating = true;
            this.isOpen = false;
            document.body.classList.remove('nav-open');
            this.nav.classList.remove('active');
            this.toggleBtn.classList.remove('active');
            this.toggleBtn.setAttribute('aria-expanded', 'false');
            this.nav.setAttribute('aria-hidden', 'true');
            if (this.overlay) {
                this.overlay.classList.remove('active');
                this.overlay.setAttribute('aria-hidden', 'true');
            }
            document.body.style.top = '';
            if (this.scrollPosition) {
                window.scrollTo(0, this.scrollPosition);
                this.scrollPosition = 0;
            }
            setTimeout(() => { this.isAnimating = false; }, 400);
            if (this._focusHandler) {
                document.removeEventListener('keydown', this._focusHandler);
                this._focusHandler = null;
            }
            this.toggleBtn.focus();
        }

        trapFocus() {
            const focusable = this.nav.querySelectorAll('a[href], button, textarea, input, select');
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            const initialFocus = this.closeBtn && this.nav.contains(this.closeBtn) ? this.closeBtn : first;
            if (initialFocus) {
                initialFocus.focus();
            }
            this._focusHandler = (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } 
                    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
                }
            };
            document.addEventListener('keydown', this._focusHandler);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        new ThemeController('wagusen_theme_v2');
        new ImageOptimizer();
        new PerformanceOptimizer();
        const mobileNav = new MobileNavigation();
        mobileNav.init();
    });
})();
