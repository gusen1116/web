/**
 * 최적화된 메인 JavaScript 파일
 * - 메모리 누수 방지
 * - 성능 최적화
 * - 모듈 패턴 적용
 * - 리소스 정리 메커니즘
 */

(function() {
    'use strict';
    
    // ===== 설정 상수 정의 =====
    const CONFIG = {
        THEME: {
            LOCAL_STORAGE_KEY: 'theme',
            DARK_CLASS: 'dark-theme',
            ANIMATION_DURATION: 200
        },
        SCROLL: {
            HEADER_HIDE_THRESHOLD: 100,
            HEADER_SHADOW_THRESHOLD: 10,
            BACK_TO_TOP_THRESHOLD: 300,
            THROTTLE_DELAY: 16, // ~60fps
            SMOOTH_BEHAVIOR: 'smooth'
        },
        INTERSECTION: {
            ROOT_MARGIN: '50px 0px',
            THRESHOLD: 0.1
        },
        PERFORMANCE: {
            IDLE_CALLBACK_TIMEOUT: 2000,
            DEBOUNCE_DELAY: 300,
            RESIZE_THROTTLE: 100
        },
        ANIMATION: {
            RIPPLE_DURATION: 600,
            SCALE_ANIMATION_DURATION: 200,
            ROTATION_ANGLE: 360
        }
    };

    // ===== 성능 유틸리티 클래스 =====
    class PerformanceUtils {
        static debounce(func, wait, immediate = false) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func.apply(this, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(this, args);
            };
        }

        static throttle(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }

        static batchDOMUpdates(updates) {
            return new Promise(resolve => {
                requestAnimationFrame(() => {
                    updates.forEach(update => update());
                    resolve();
                });
            });
        }

        static measurePerformance(name, fn) {
            const start = performance.now();
            const result = fn();
            const end = performance.now();
            console.log(`${name}: ${end - start} milliseconds`);
            return result;
        }
    }

    // ===== 메모리 관리 클래스 =====
    class MemoryManager {
        constructor() {
            this.eventListeners = new Map();
            this.observers = new Set();
            this.intervals = new Set();
            this.timeouts = new Set();
            this.animationFrames = new Set();
        }

        addEventListener(element, event, handler, options = {}) {
            const key = `${element.constructor.name}-${event}`;
            if (!this.eventListeners.has(key)) {
                this.eventListeners.set(key, []);
            }
            
            element.addEventListener(event, handler, options);
            this.eventListeners.get(key).push({ element, event, handler, options });
        }

        addObserver(observer) {
            this.observers.add(observer);
        }

        addInterval(id) {
            this.intervals.add(id);
        }

        addTimeout(id) {
            this.timeouts.add(id);
        }

        addAnimationFrame(id) {
            this.animationFrames.add(id);
        }

        cleanup() {
            // 이벤트 리스너 정리
            this.eventListeners.forEach(listeners => {
                listeners.forEach(({ element, event, handler, options }) => {
                    element.removeEventListener(event, handler, options);
                });
            });
            this.eventListeners.clear();

            // Observer 정리
            this.observers.forEach(observer => {
                if (observer && typeof observer.disconnect === 'function') {
                    observer.disconnect();
                }
            });
            this.observers.clear();

            // 타이머 정리
            this.intervals.forEach(id => clearInterval(id));
            this.intervals.clear();

            this.timeouts.forEach(id => clearTimeout(id));
            this.timeouts.clear();

            // 애니메이션 프레임 정리
            this.animationFrames.forEach(id => cancelAnimationFrame(id));
            this.animationFrames.clear();
        }
    }

    // ===== DOM 캐시 관리 클래스 =====
    class DOMCache {
        constructor() {
            this.cache = new Map();
            this.computedCache = new Map();
        }

        get(selector) {
            if (!this.cache.has(selector)) {
                const element = document.querySelector(selector);
                if (element) {
                    this.cache.set(selector, element);
                }
            }
            return this.cache.get(selector);
        }

        getAll(selector) {
            const cacheKey = `all-${selector}`;
            if (!this.cache.has(cacheKey)) {
                const elements = document.querySelectorAll(selector);
                this.cache.set(cacheKey, elements);
            }
            return this.cache.get(cacheKey);
        }

        getComputedStyle(element, property) {
            const cacheKey = `${element.tagName}-${property}`;
            if (!this.computedCache.has(cacheKey)) {
                const style = window.getComputedStyle(element);
                this.computedCache.set(cacheKey, style[property]);
            }
            return this.computedCache.get(cacheKey);
        }

        invalidate(selector = null) {
            if (selector) {
                this.cache.delete(selector);
                this.cache.delete(`all-${selector}`);
            } else {
                this.cache.clear();
            }
            this.computedCache.clear();
        }
    }

    // ===== 메인 애플리케이션 클래스 =====
    class MainApplication {
        constructor() {
            this.memoryManager = new MemoryManager();
            this.domCache = new DOMCache();
            this.isInitialized = false;
            this.scrollState = {
                lastScrollY: 0,
                ticking: false,
                headerHeight: 0
            };
            
            // 바인드된 메서드들 (메모리 효율성을 위해)
            this.boundHandlers = {
                scroll: PerformanceUtils.throttle(this.handleScroll.bind(this), CONFIG.SCROLL.THROTTLE_DELAY),
                resize: PerformanceUtils.throttle(this.handleResize.bind(this), CONFIG.PERFORMANCE.RESIZE_THROTTLE),
                beforeUnload: this.handleBeforeUnload.bind(this),
                visibilityChange: this.handleVisibilityChange.bind(this)
            };
        }

        init() {
            if (this.isInitialized) {
                console.warn('Application already initialized');
                return;
            }

            try {
                this.cacheInitialElements();
                this.initializeTheme();
                this.initializeMobileMenu();
                this.initializeScrollEffects();
                this.initializeAccessibility();
                this.initializeOptimizations();
                this.setupEventListeners();
                this.setupPageTransitions();
                
                this.isInitialized = true;
                console.log('Main application initialized successfully');
            } catch (error) {
                console.error('Failed to initialize main application:', error);
            }
        }

        cacheInitialElements() {
            // 자주 사용되는 DOM 요소들을 미리 캐시
            const selectors = [
                '.top-header',
                '#theme-toggle',
                '#mobile-theme-toggle',
                '#mobile-toggle',
                '#mobile-nav',
                '#mobile-nav-close',
                '#mobile-overlay',
                '.mobile-nav-link'
            ];

            selectors.forEach(selector => this.domCache.get(selector));
            
            // 헤더 높이 캐시
            const header = this.domCache.get('.top-header');
            if (header) {
                this.scrollState.headerHeight = header.offsetHeight;
            }
        }

        initializeTheme() {
            const themeToggle = this.domCache.get('#theme-toggle');
            const mobileThemeToggle = this.domCache.get('#mobile-theme-toggle');
            const htmlElement = document.documentElement;
            
            // 현재 테마 상태 확인 및 적용
            const currentTheme = this.getCurrentTheme();
            this.applyTheme(currentTheme, false);
            
            // 테마 토글 이벤트
            if (themeToggle) {
                this.memoryManager.addEventListener(
                    themeToggle, 
                    'click', 
                    this.createThemeToggleHandler(themeToggle)
                );
            }
            
            if (mobileThemeToggle) {
                this.memoryManager.addEventListener(
                    mobileThemeToggle, 
                    'click', 
                    this.createThemeToggleHandler()
                );
            }
        }

        getCurrentTheme() {
            try {
                return localStorage.getItem(CONFIG.THEME.LOCAL_STORAGE_KEY) || 'light';
            } catch (e) {
                console.warn('LocalStorage not available, using default theme');
                return 'light';
            }
        }

        applyTheme(theme, animate = true) {
            const htmlElement = document.documentElement;
            const mobileThemeToggle = this.domCache.get('#mobile-theme-toggle');
            
            // DOM 업데이트를 배치로 처리
            const updates = [
                () => {
                    if (theme === 'dark') {
                        htmlElement.classList.add(CONFIG.THEME.DARK_CLASS);
                    } else {
                        htmlElement.classList.remove(CONFIG.THEME.DARK_CLASS);
                    }
                },
                () => {
                    if (mobileThemeToggle) {
                        const slider = mobileThemeToggle.querySelector('.theme-switch-slider');
                        if (slider) {
                            slider.classList.toggle('active', theme === 'dark');
                        }
                    }
                }
            ];
            
            PerformanceUtils.batchDOMUpdates(updates);
        }

        createThemeToggleHandler(buttonElement = null) {
            return () => {
                const currentTheme = this.getCurrentTheme();
                const newTheme = currentTheme === 'light' ? 'dark' : 'light';
                
                try {
                    localStorage.setItem(CONFIG.THEME.LOCAL_STORAGE_KEY, newTheme);
                } catch (e) {
                    console.warn('Failed to save theme preference');
                }
                
                this.applyTheme(newTheme);
                
                // 시각적 피드백 (애니메이션)
                if (buttonElement) {
                    this.animateThemeButton(buttonElement);
                }
            };
        }

        animateThemeButton(button) {
            const originalTransform = button.style.transform;
            button.style.transform = 'scale(0.8) rotate(180deg)';
            
            const timeoutId = setTimeout(() => {
                button.style.transform = originalTransform;
                this.memoryManager.timeouts.delete(timeoutId);
            }, CONFIG.THEME.ANIMATION_DURATION);
            
            this.memoryManager.addTimeout(timeoutId);
        }

        initializeMobileMenu() {
            const mobileToggle = this.domCache.get('#mobile-toggle');
            const mobileNav = this.domCache.get('#mobile-nav');
            const mobileNavClose = this.domCache.get('#mobile-nav-close');
            const mobileOverlay = this.domCache.get('#mobile-overlay');
            const mobileNavLinks = this.domCache.getAll('.mobile-nav-link');
            
            if (!mobileToggle || !mobileNav) return;
            
            const openMenu = () => this.setMobileMenuState(true);
            const closeMenu = () => this.setMobileMenuState(false);
            
            // 이벤트 리스너 등록
            this.memoryManager.addEventListener(mobileToggle, 'click', openMenu);
            
            if (mobileNavClose) {
                this.memoryManager.addEventListener(mobileNavClose, 'click', closeMenu);
            }
            
            if (mobileOverlay) {
                this.memoryManager.addEventListener(mobileOverlay, 'click', closeMenu);
            }
            
            // 네비게이션 링크 클릭시 메뉴 닫기 (테마 토글 제외)
            if (mobileNavLinks) {
                Array.from(mobileNavLinks).forEach(link => {
                    if (!link.querySelector('.theme-switch')) {
                        this.memoryManager.addEventListener(link, 'click', closeMenu);
                    }
                });
            }
            
            // ESC 키로 메뉴 닫기
            this.memoryManager.addEventListener(document, 'keydown', (e) => {
                if (e.key === 'Escape' && mobileNav.classList.contains('active')) {
                    closeMenu();
                }
            });
        }

        setMobileMenuState(isOpen) {
            const mobileNav = this.domCache.get('#mobile-nav');
            const mobileOverlay = this.domCache.get('#mobile-overlay');
            const mobileToggle = this.domCache.get('#mobile-toggle');
            
            const updates = [
                () => {
                    if (mobileNav) mobileNav.classList.toggle('active', isOpen);
                    if (mobileOverlay) mobileOverlay.classList.toggle('active', isOpen);
                    if (mobileToggle) mobileToggle.classList.toggle('active', isOpen);
                    document.body.classList.toggle('nav-open', isOpen);
                }
            ];
            
            PerformanceUtils.batchDOMUpdates(updates);
        }

        initializeScrollEffects() {
            // 스크롤 진행률 표시기 생성
            this.createScrollProgress();
            
            // Back to top 버튼 생성
            this.createBackToTopButton();
            
            // 메인 스크롤 이벤트 등록
            this.memoryManager.addEventListener(window, 'scroll', this.boundHandlers.scroll, { passive: true });
        }

        handleScroll() {
            if (this.scrollState.ticking) return;
            
            this.scrollState.ticking = true;
            
            const frameId = requestAnimationFrame(() => {
                this.updateScrollEffects();
                this.scrollState.ticking = false;
                this.memoryManager.animationFrames.delete(frameId);
            });
            
            this.memoryManager.addAnimationFrame(frameId);
        }

        updateScrollEffects() {
            const currentScrollY = window.pageYOffset;
            const header = this.domCache.get('.top-header');
            const backToTopButton = this.domCache.get('.back-to-top');
            const scrollProgress = this.domCache.get('.scroll-progress');
            
            // 헤더 효과 업데이트
            if (header) {
                const updates = [];
                
                // 헤더 숨김/표시
                if (currentScrollY > this.scrollState.lastScrollY && currentScrollY > CONFIG.SCROLL.HEADER_HIDE_THRESHOLD) {
                    updates.push(() => header.classList.add('header-hidden'));
                } else {
                    updates.push(() => header.classList.remove('header-hidden'));
                }
                
                // 헤더 그림자
                if (currentScrollY > CONFIG.SCROLL.HEADER_SHADOW_THRESHOLD) {
                    updates.push(() => header.classList.add('header-shadow'));
                } else {
                    updates.push(() => header.classList.remove('header-shadow'));
                }
                
                PerformanceUtils.batchDOMUpdates(updates);
            }
            
            // Back to top 버튼
            if (backToTopButton) {
                const isVisible = currentScrollY > CONFIG.SCROLL.BACK_TO_TOP_THRESHOLD;
                backToTopButton.classList.toggle('visible', isVisible);
            }
            
            // 스크롤 진행률
            if (scrollProgress) {
                const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
                const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
                const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
                scrollProgress.style.width = Math.min(scrolled, 100) + '%';
            }
            
            this.scrollState.lastScrollY = currentScrollY;
        }

        createScrollProgress() {
            const scrollProgress = document.createElement('div');
            scrollProgress.className = 'scroll-progress';
            scrollProgress.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 0%;
                height: 3px;
                background: linear-gradient(90deg, var(--primary-400), var(--primary-600));
                z-index: var(--z-tooltip);
                transition: width 0.3s ease;
                pointer-events: none;
            `;
            document.body.appendChild(scrollProgress);
            this.domCache.cache.set('.scroll-progress', scrollProgress);
        }

        createBackToTopButton() {
            const backToTopButton = document.createElement('button');
            backToTopButton.className = 'back-to-top';
            backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
            backToTopButton.setAttribute('aria-label', '맨 위로 이동');
            backToTopButton.style.cssText = `
                position: fixed;
                bottom: var(--space-8);
                right: var(--space-8);
                width: 48px;
                height: 48px;
                background: var(--primary-500);
                color: white;
                border: none;
                border-radius: var(--radius-full);
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: var(--shadow-lg);
                cursor: pointer;
                opacity: 0;
                visibility: hidden;
                transition: all var(--duration-300) var(--ease-out);
                z-index: var(--z-fixed);
            `;
            
            // 클릭 이벤트
            this.memoryManager.addEventListener(backToTopButton, 'click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: CONFIG.SCROLL.SMOOTH_BEHAVIOR
                });
            });
            
            document.body.appendChild(backToTopButton);
            this.domCache.cache.set('.back-to-top', backToTopButton);
        }

        initializeAccessibility() {
            let isTabbing = false;
            
            // 키보드 포커스 감지
            this.memoryManager.addEventListener(window, 'keydown', (e) => {
                if (e.key === 'Tab') {
                    isTabbing = true;
                    document.body.classList.add('keyboard-focus-visible');
                }
            });
            
            this.memoryManager.addEventListener(window, 'mousedown', () => {
                isTabbing = false;
                document.body.classList.remove('keyboard-focus-visible');
            });
            
            // 부드러운 스크롤 앵커 링크 처리
            const anchorLinks = this.domCache.getAll('a[href^="#"]');
            if (anchorLinks) {
                Array.from(anchorLinks).forEach(anchor => {
                    this.memoryManager.addEventListener(anchor, 'click', (e) => {
                        e.preventDefault();
                        const targetId = anchor.getAttribute('href');
                        const targetElement = document.querySelector(targetId);
                        
                        if (targetElement) {
                            const targetPosition = targetElement.offsetTop - this.scrollState.headerHeight - 20;
                            window.scrollTo({
                                top: targetPosition,
                                behavior: CONFIG.SCROLL.SMOOTH_BEHAVIOR
                            });
                        }
                    });
                });
            }
        }

        initializeOptimizations() {
            // 이미지 지연 로딩 최적화
            this.setupLazyLoading();
            
            // 외부 링크 처리
            this.setupExternalLinks();
            
            // 리사이즈 이벤트 최적화
            this.memoryManager.addEventListener(window, 'resize', this.boundHandlers.resize, { passive: true });
            
            // 페이지 언로드 시 정리
            this.memoryManager.addEventListener(window, 'beforeunload', this.boundHandlers.beforeUnload);
            
            // 페이지 가시성 변경 감지
            this.memoryManager.addEventListener(document, 'visibilitychange', this.boundHandlers.visibilityChange);
        }

        setupLazyLoading() {
            const lazyImages = this.domCache.getAll('img[data-src]');
            if (!lazyImages || lazyImages.length === 0) return;
            
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            img.classList.add('fade-in');
                            observer.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: CONFIG.INTERSECTION.ROOT_MARGIN
                });
                
                Array.from(lazyImages).forEach(img => imageObserver.observe(img));
                this.memoryManager.addObserver(imageObserver);
            } else {
                // 폴백: IntersectionObserver 미지원 브라우저
                Array.from(lazyImages).forEach(img => {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                });
            }
        }

        setupExternalLinks() {
            const externalLinks = this.domCache.getAll('a[href^="http"]');
            if (!externalLinks) return;
            
            Array.from(externalLinks).forEach(link => {
                if (!link.href.includes(window.location.hostname)) {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                }
            });
        }

        handleResize() {
            // DOM 캐시 무효화 (크기 관련)
            this.domCache.invalidate();
            
            // 헤더 높이 재계산
            const header = this.domCache.get('.top-header');
            if (header) {
                this.scrollState.headerHeight = header.offsetHeight;
            }
        }

        handleBeforeUnload() {
            // 메모리 정리
            this.cleanup();
        }

        handleVisibilityChange() {
            // 페이지가 숨겨지면 불필요한 작업 중지
            if (document.hidden) {
                // 애니메이션 일시 중지 등의 작업 수행 가능
                console.log('Page hidden, reducing activity');
            } else {
                console.log('Page visible, resuming activity');
            }
        }

        setupEventListeners() {
            // 전역 에러 핸들링
            this.memoryManager.addEventListener(window, 'error', (e) => {
                console.error('Global error:', e.error);
            });
            
            // Promise rejection 핸들링
            this.memoryManager.addEventListener(window, 'unhandledrejection', (e) => {
                console.error('Unhandled promise rejection:', e.reason);
            });
        }

        setupPageTransitions() {
            const pageContent = this.domCache.get('main');
            if (pageContent) {
                pageContent.classList.add('page-transition', 'fade-in');
            }
            
            // Idle callback으로 무거운 작업 지연
            if ('requestIdleCallback' in window) {
                requestIdleCallback(() => {
                    this.performIdleOptimizations();
                }, { timeout: CONFIG.PERFORMANCE.IDLE_CALLBACK_TIMEOUT });
            }
        }

        performIdleOptimizations() {
            // 브라우저가 한가할 때 수행할 최적화 작업들
            console.log('Performing idle optimizations');
            
            // 예: 프리로드할 이미지나 리소스 준비
            // 예: 사용자 행동 분석 데이터 전송
            // 예: 캐시 최적화
        }

        cleanup() {
            console.log('Cleaning up main application');
            this.memoryManager.cleanup();
            this.domCache.cache.clear();
            this.domCache.computedCache.clear();
            this.isInitialized = false;
        }

        // 공개 API 메서드들
        getTheme() {
            return this.getCurrentTheme();
        }

        toggleTheme() {
            const themeToggle = this.domCache.get('#theme-toggle');
            if (themeToggle) {
                themeToggle.click();
            }
        }

        scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: CONFIG.SCROLL.SMOOTH_BEHAVIOR
            });
        }
    }

    // ===== 전역 유틸리티 함수들 (이전 버전과의 호환성) =====
    const utils = {
        debounce: PerformanceUtils.debounce,
        throttle: PerformanceUtils.throttle,
        safeLocalStorage: () => {
            try {
                const testKey = '__test__';
                localStorage.setItem(testKey, 'test');
                localStorage.removeItem(testKey);
                return true;
            } catch (e) {
                return false;
            }
        }
    };

    // ===== 애플리케이션 초기화 =====
    let app = null;
    
    function initializeApplication() {
        if (app) {
            console.warn('Application already exists');
            return app;
        }
        
        app = new MainApplication();
        app.init();
        
        // 전역 객체에 앱 인스턴스 노출 (디버깅용)
        if (typeof window !== 'undefined') {
            window.WagusenApp = app;
            window.WagusenUtils = utils;
        }
        
        return app;
    }

    // DOM 준비 완료 시 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApplication);
    } else {
        // DOM이 이미 로드된 경우
        initializeApplication();
    }

    // 모듈 시스템 지원
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { MainApplication, PerformanceUtils, MemoryManager, DOMCache };
    }

})();