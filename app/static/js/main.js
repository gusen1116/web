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
            // DOM 로드 완료 시 기존 이미지 최적화
            this.optimizeExistingImages();
            
            // Intersection Observer 설정 (지연 로딩)
            this.setupIntersectionObserver();
            
            // 동적으로 추가되는 이미지 감지
            this.setupMutationObserver();
        }

        optimizeExistingImages() {
            const images = document.querySelectorAll('img');
            images.forEach(img => this.optimizeImage(img));
        }

        optimizeImage(img) {
            // 이미 처리된 이미지는 건너뛰기
            if (this.processedImages.has(img)) return;

            // 로딩 및 디코딩 최적화 적용
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            if (!img.hasAttribute('decoding')) {
                img.setAttribute('decoding', 'async');
            }

            // 이미지 로딩 상태 관리
            this.setupImageLoadingStates(img);

            // 처리 완료 표시
            this.processedImages.add(img);
        }

        setupImageLoadingStates(img) {
            // 로딩 상태 클래스 추가
            img.classList.add('lazy-image');

            // 이미지 로드 완료 시
            const handleLoad = () => {
                img.classList.add('loaded');
                img.removeEventListener('load', handleLoad);
                img.removeEventListener('error', handleError);
            };

            // 이미지 로드 실패 시
            const handleError = () => {
                img.classList.add('error');
                console.warn('이미지 로딩 실패:', img.src);
                img.removeEventListener('load', handleLoad);
                img.removeEventListener('error', handleError);
            };

            // 이미 로드된 경우
            if (img.complete && img.naturalHeight !== 0) {
                handleLoad();
            } else {
                img.addEventListener('load', handleLoad, { passive: true });
                img.addEventListener('error', handleError, { passive: true });
            }
        }

        setupIntersectionObserver() {
            // Intersection Observer 지원 확인
            if (!('IntersectionObserver' in window)) return;

            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        
                        // 뷰포트에 들어온 이미지 처리
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                        }
                        
                        // 관찰 중지
                        this.observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px',
                threshold: 0.1
            });

            // data-src 속성을 가진 이미지들 관찰
            document.querySelectorAll('img[data-src]').forEach(img => {
                this.observer.observe(img);
            });
        }

        setupMutationObserver() {
            // 동적으로 추가되는 이미지 감지
            const mutationObserver = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // 추가된 노드가 이미지인 경우
                            if (node.tagName === 'IMG') {
                                this.optimizeImage(node);
                                if (node.dataset.src && this.observer) {
                                    this.observer.observe(node);
                                }
                            }
                            
                            // 추가된 노드 내부의 이미지들
                            const images = node.querySelectorAll('img');
                            images.forEach(img => {
                                this.optimizeImage(img);
                                if (img.dataset.src && this.observer) {
                                    this.observer.observe(img);
                                }
                            });
                        }
                    });
                });
            });

            mutationObserver.observe(document.body, {
                childList: true,
                subtree: true
            });
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
            // 애니메이션 최적화
            this.optimizeAnimations();
            
            // 스크롤 성능 최적화
            this.optimizeScrolling();
            
            // 폰트 로딩 최적화
            this.optimizeFonts();
        }

        optimizeAnimations() {
            // will-change 속성 동적 관리
            const elementsWithTransitions = document.querySelectorAll('[class*="transition"], [class*="hover"], .card, .btn, .post-card');
            
            elementsWithTransitions.forEach(element => {
                if (this.animationElements.has(element)) return;

                // 호버/포커스 시작
                const startAnimation = () => {
                    element.style.willChange = 'transform, opacity';
                };

                // 호버/포커스 종료
                const endAnimation = () => {
                    element.style.willChange = 'auto';
                };

                // 트랜지션 종료
                const transitionEnd = () => {
                    element.style.willChange = 'auto';
                };

                element.addEventListener('mouseenter', startAnimation, { passive: true });
                element.addEventListener('focusin', startAnimation, { passive: true });
                element.addEventListener('mouseleave', endAnimation, { passive: true });
                element.addEventListener('focusout', endAnimation, { passive: true });
                element.addEventListener('transitionend', transitionEnd, { passive: true });

                this.animationElements.add(element);
            });
        }

        optimizeScrolling() {
            // 스크롤 이벤트 쓰로틀링
            let ticking = false;

            const updateScrollElements = () => {
                // 페이드인 애니메이션 처리
                const fadeElements = document.querySelectorAll('.fade-in:not(.animation-complete)');
                
                fadeElements.forEach(element => {
                    const rect = element.getBoundingClientRect();
                    const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
                    
                    if (isVisible) {
                        element.classList.add('animation-complete');
                        // 애니메이션 완료 후 will-change 제거
                        setTimeout(() => {
                            element.style.willChange = 'auto';
                        }, 500);
                    }
                });

                ticking = false;
            };

            const requestTick = () => {
                if (!ticking) {
                    requestAnimationFrame(updateScrollElements);
                    ticking = true;
                }
            };

            window.addEventListener('scroll', requestTick, { passive: true });
            window.addEventListener('resize', requestTick, { passive: true });

            // 초기 실행
            requestTick();
        }

        optimizeFonts() {
            // 폰트 로딩 완료 감지
            if ('fonts' in document) {
                document.fonts.ready.then(() => {
                    document.body.classList.add('fonts-loaded');
                    
                    // 폰트 로딩 완료 후 리플로우 최소화
                    const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div');
                    textElements.forEach(element => {
                        element.style.fontDisplay = 'swap';
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

            // 4. 테마 변경 이벤트 발송
            this.dispatchThemeChangeEvent(theme);
        }

        dispatchThemeChangeEvent(theme) {
            const event = new CustomEvent('themeChanged', {
                detail: { theme: theme.name, className: theme.className }
            });
            document.dispatchEvent(event);
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
            this.toggle = $('#mobileToggle');
            this.nav = $('#mobileNav');
            this.close = $('#mobileNavClose');
            this.overlay = $('#mobileOverlay');
            this.isAnimating = false;
        }
        
        init() {
            if (!this.toggle || !this.nav) return;
            
            // 이벤트 위임 사용
            this.toggle.addEventListener('click', this.handleToggleClick.bind(this), { passive: false });
            
            if (this.close) {
                this.close.addEventListener('click', this.handleCloseClick.bind(this), { passive: false });
            }
            
            if (this.overlay) {
                this.overlay.addEventListener('click', this.handleOverlayClick.bind(this), { passive: false });
            }

            // ESC 키로 메뉴 닫기
            document.addEventListener('keydown', this.handleKeydown.bind(this), { passive: false });

            // 리사이즈 시 메뉴 상태 확인
            window.addEventListener('resize', this.handleResize.bind(this), { passive: true });
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
            // 데스크톱 크기로 변경 시 모바일 메뉴 자동 닫기
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

            // will-change 최적화
            this.nav.style.willChange = 'transform';
            if (this.overlay) this.overlay.style.willChange = 'opacity';

            document.body.classList.add('nav-open');
            this.nav.classList.add('active');
            this.toggle.classList.add('active');
            
            if (this.overlay) {
                this.overlay.classList.add('active');
            }

            // 애니메이션 완료 후 will-change 제거
            setTimeout(() => {
                this.nav.style.willChange = 'auto';
                if (this.overlay) this.overlay.style.willChange = 'auto';
                this.isAnimating = false;
            }, 400);

            // 접근성: 포커스 트래핑
            this.trapFocus();
        }
        
        closeMenu() {
            if (!this.isOpen || this.isAnimating) return;
            
            this.isAnimating = true;
            this.isOpen = false;

            // will-change 최적화
            this.nav.style.willChange = 'transform';
            if (this.overlay) this.overlay.style.willChange = 'opacity';
            
            document.body.classList.remove('nav-open');
            this.nav.classList.remove('active');
            this.toggle.classList.remove('active');
            
            if (this.overlay) {
                this.overlay.classList.remove('active');
            }

            // 애니메이션 완료 후 will-change 제거
            setTimeout(() => {
                this.nav.style.willChange = 'auto';
                if (this.overlay) this.overlay.style.willChange = 'auto';
                this.isAnimating = false;
            }, 400);

            // 포커스 복원
            this.toggle.focus();
        }

        trapFocus() {
            if (!this.isOpen) return;

            const focusableElements = this.nav.querySelectorAll(
                'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
            );
            
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            const trapFocusHandler = (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            lastElement.focus();
                            e.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            firstElement.focus();
                            e.preventDefault();
                        }
                    }
                }
            };

            document.addEventListener('keydown', trapFocusHandler);

            // 메뉴 닫을 때 이벤트 리스너 제거
            const removeListener = () => {
                document.removeEventListener('keydown', trapFocusHandler);
            };

            // 첫 번째 요소에 포커스
            if (firstElement) firstElement.focus();

            return removeListener;
        }
    }

    /**
     * 메모리 관리 및 정리 클래스
     */
    class ResourceManager {
        constructor() {
            this.cleanupTasks = [];
            this.intervalId = null;
            this.init();
        }

        init() {
            // 주기적인 메모리 정리
            this.intervalId = setInterval(() => {
                this.performCleanup();
            }, 30000); // 30초마다

            // 페이지 언로드 시 정리
            window.addEventListener('beforeunload', () => {
                this.destroy();
            });
        }

        addCleanupTask(task) {
            this.cleanupTasks.push(task);
        }

        performCleanup() {
            // WeakSet과 WeakMap은 자동으로 정리되므로 별도 처리 불필요
            
            // DOM에서 제거된 요소들의 이벤트 리스너 정리
            const elements = document.querySelectorAll('[data-cleanup-needed]');
            elements.forEach(element => {
                if (!document.contains(element)) {
                    element.removeAttribute('data-cleanup-needed');
                }
            });

            // 커스텀 정리 작업 실행
            this.cleanupTasks.forEach(task => {
                try {
                    task();
                } catch (error) {
                    console.warn('정리 작업 실행 중 오류:', error);
                }
            });
        }

        destroy() {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }

            // 모든 정리 작업 실행
            this.performCleanup();
            this.cleanupTasks = [];
        }
    }

    /**
     * DOM 로드 완료 시 초기화
     */
    function initOnDOMLoad() {
        // 리소스 관리자 초기화
        const resourceManager = new ResourceManager();

        // 이미지 최적화 초기화
        const imageOptimizer = new ImageOptimizer();
        resourceManager.addCleanupTask(() => imageOptimizer.destroy());

        // 성능 최적화 초기화
        const performanceOptimizer = new PerformanceOptimizer();

        // 모바일 내비게이션 초기화
        const mobileNav = new MobileNavigation();
        mobileNav.init();

        // 통합 테마 컨트롤러 초기화
        const themeController = new ThemeController('wagusen_theme_v2');
        
        // 통합 테마 토글 버튼 이벤트 리스너
        const unifiedThemeToggle = $('#unifiedThemeToggle');
        if (unifiedThemeToggle) {
            unifiedThemeToggle.addEventListener('click', () => {
                themeController.toggle();
            }, { passive: false });
        }

        // 개발 모드에서 전역 접근 허용
        if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
            window.WagusenOptimizers = {
                imageOptimizer,
                performanceOptimizer,
                themeController,
                mobileNav,
                resourceManager
            };
        }

        // 초기화 완료 이벤트
        document.dispatchEvent(new CustomEvent('wagusenInitialized', {
            detail: { 
                version: '2.0',
                optimizers: ['image', 'performance', 'theme', 'navigation'] 
            }
        }));

        console.log('🚀 Wagusen 최적화 시스템 초기화 완료');
    }

    // DOM 로드 완료 시 초기화 함수 실행
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOnDOMLoad);
    } else {
        initOnDOMLoad();
    }

    // 모듈 시스템 지원
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            ImageOptimizer,
            PerformanceOptimizer,
            ThemeController,
            MobileNavigation,
            ResourceManager
        };
    }
})();