// main.js - 개선된 통합 스크립트 (중복 제거 및 모듈화)

/**
 * 와구센 블로그 메인 애플리케이션
 * 테마 관리, 모바일 네비게이션, 스크롤 효과, 포스트 카드 기능을 통합 관리
 */
const WagusenApp = {
    // 설정 객체 - 하드코딩된 값들을 한 곳에서 관리
    config: {
        breakpoints: {
            mobile: 768,
            small: 480
        },
        animation: {
            duration: 300,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        },
        cache: {
            timeout: 300000 // 5분
        },
        scroll: {
            hideHeaderThreshold: 100,
            throttleDelay: 16 // ~60fps
        }
    },
    
    // 상태 관리 - 앱의 현재 상태를 중앙에서 관리
    state: {
        isMobileMenuOpen: false,
        currentTheme: null, // 초기화 시 설정됨
        scrollPosition: 0,
        lastScrollTop: 0,
        isScrolling: false
    },
    
    // DOM 요소 캐시 - 자주 사용되는 DOM 요소들을 미리 찾아서 저장
    elements: {
        // 테마 관련
        html: document.documentElement,
        body: document.body,
        
        // 모바일 메뉴 관련
        mobileToggle: null,
        mobileNav: null,
        mobileNavClose: null,
        mobileOverlay: null,
        mobileNavLinks: null,
        
        // 테마 토글 관련
        desktopThemeToggle: null,
        mobileThemeToggle: null,
        themeText: null,
        themeSwitch: null,
        
        // 헤더 관련
        header: null
    },
    
    /**
     * 애플리케이션 초기화
     * DOM이 로드된 후 모든 기능을 초기화합니다
     */
    init() {
        try {
            this.cacheElements();
            this.theme.init();
            this.navigation.init();
            this.scroll.init();
            this.postCards.init();
            this.bindGlobalEvents();
            
            console.log('와구센 블로그 애플리케이션 초기화 완료');
        } catch (error) {
            this.handleError(error, '애플리케이션 초기화');
        }
    },
    
    /**
     * DOM 요소들을 미리 찾아서 캐시
     * 성능 최적화를 위해 자주 사용되는 요소들을 미리 저장
     */
    cacheElements() {
        // 모바일 메뉴 요소들
        this.elements.mobileToggle = document.getElementById('mobileToggle');
        this.elements.mobileNav = document.getElementById('mobileNav');
        this.elements.mobileNavClose = document.getElementById('mobileNavClose');
        this.elements.mobileOverlay = document.getElementById('mobileOverlay');
        this.elements.mobileNavLinks = document.querySelectorAll('.mobile-nav-link:not(.mobile-theme-toggle)');
        
        // 테마 토글 요소들
        this.elements.desktopThemeToggle = document.getElementById('themeToggle');
        this.elements.mobileThemeToggle = document.getElementById('mobileThemeToggle');
        this.elements.themeText = document.querySelector('.theme-text');
        this.elements.themeSwitch = document.querySelector('.theme-switch-slider');
        
        // 헤더 요소
        this.elements.header = document.getElementById('siteHeader');
    },
    
    /**
     * 테마 관리 모듈
     * 다크/라이트 모드 전환과 관련된 모든 기능을 담당
     */
    theme: {
        /**
         * 테마 시스템 초기화
         * 저장된 설정이나 시스템 설정에 따라 초기 테마를 설정
         */
        init() {
            // 저장된 테마 설정을 확인 (localStorage에서)
            const savedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            // 테마 결정 로직: 저장된 설정 > 시스템 설정 > 기본값(라이트)
            if (savedTheme) {
                WagusenApp.state.currentTheme = savedTheme;
            } else if (prefersDark) {
                WagusenApp.state.currentTheme = 'dark';
            } else {
                WagusenApp.state.currentTheme = 'light';
            }
            
            // 테마 적용
            this.apply(WagusenApp.state.currentTheme);
            this.updateUI();
            this.bindEvents();
            
            // 시스템 테마 변경 감지
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.apply(newTheme);
                    WagusenApp.state.currentTheme = newTheme;
                    this.updateUI();
                }
            });
        },
        
        /**
         * 테마 적용
         * HTML 요소에 dark-theme 클래스를 추가/제거하여 테마를 변경
         */
        apply(theme) {
            const isDark = theme === 'dark';
            
            WagusenApp.elements.html.classList.toggle('dark-theme', isDark);
            WagusenApp.elements.body.classList.toggle('dark-theme', isDark);
            
            // CSS 변수 재계산을 위한 강제 리플로우
            WagusenApp.elements.body.offsetHeight;
        },
        
        /**
         * 테마 토글
         * 현재 테마를 반대 테마로 전환
         */
        toggle() {
            const newTheme = WagusenApp.state.currentTheme === 'dark' ? 'light' : 'dark';
            
            this.apply(newTheme);
            localStorage.setItem('theme', newTheme);
            WagusenApp.state.currentTheme = newTheme;
            this.updateUI();
            
            console.log('테마 변경:', newTheme);
        },
        
        /**
         * UI 업데이트
         * 테마 변경에 따라 관련 UI 요소들을 업데이트
         */
        updateUI() {
            const isDark = WagusenApp.state.currentTheme === 'dark';
            
            if (WagusenApp.elements.themeText) {
                WagusenApp.elements.themeText.textContent = isDark ? '다크모드' : '라이트모드';
            }
            
            if (WagusenApp.elements.themeSwitch) {
                WagusenApp.elements.themeSwitch.classList.toggle('active', isDark);
            }
        },
        
        /**
         * 테마 관련 이벤트 바인딩
         * 데스크톱과 모바일 테마 토글 버튼에 이벤트 리스너 등록
         */
        bindEvents() {
            // 데스크톱 테마 토글 버튼
            if (WagusenApp.elements.desktopThemeToggle) {
                WagusenApp.elements.desktopThemeToggle.addEventListener('click', () => {
                    this.toggle();
                });
            }
            
            // 모바일 테마 토글 버튼
            if (WagusenApp.elements.mobileThemeToggle) {
                WagusenApp.elements.mobileThemeToggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.toggle();
                    
                    // 시각적 피드백 효과
                    const button = e.currentTarget;
                    button.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        button.style.transform = '';
                    }, 150);
                });
            }
        }
    },
    
    /**
     * 네비게이션 관리 모듈
     * 모바일 메뉴의 열기/닫기와 관련된 모든 기능을 담당
     */
    navigation: {
        /**
         * 네비게이션 시스템 초기화
         */
        init() {
            if (!WagusenApp.elements.mobileToggle) return;
            
            this.bindEvents();
            console.log('모바일 네비게이션 초기화 완료');
        },
        
        /**
         * 모바일 메뉴 열기
         */
        open() {
            WagusenApp.state.isMobileMenuOpen = true;
            
            const { mobileNav, mobileToggle, mobileOverlay, body } = WagusenApp.elements;
            
            // 활성화 클래스 추가
            if (mobileNav) mobileNav.classList.add('active');
            if (mobileToggle) mobileToggle.classList.add('active');
            if (mobileOverlay) mobileOverlay.classList.add('active');
            if (body) body.classList.add('nav-open');
            
            // 배경 스크롤 차단
            WagusenApp.state.scrollPosition = window.scrollY;
            body.style.cssText = `
                overflow: hidden;
                position: fixed;
                top: -${WagusenApp.state.scrollPosition}px;
                width: 100%;
            `;
            
            // 접근성을 위한 포커스 관리
            setTimeout(() => {
                if (WagusenApp.elements.mobileNavClose) {
                    WagusenApp.elements.mobileNavClose.focus();
                }
            }, WagusenApp.config.animation.duration);
        },
        
        /**
         * 모바일 메뉴 닫기
         */
        close() {
            WagusenApp.state.isMobileMenuOpen = false;
            
            const { mobileNav, mobileToggle, mobileOverlay, body } = WagusenApp.elements;
            
            // 활성화 클래스 제거
            if (mobileNav) mobileNav.classList.remove('active');
            if (mobileToggle) mobileToggle.classList.remove('active');
            if (mobileOverlay) mobileOverlay.classList.remove('active');
            if (body) body.classList.remove('nav-open');
            
            // 스크롤 위치 복원
            body.style.cssText = '';
            window.scrollTo(0, WagusenApp.state.scrollPosition);
        },
        
        /**
         * 모바일 메뉴 토글
         */
        toggle() {
            if (WagusenApp.state.isMobileMenuOpen) {
                this.close();
            } else {
                this.open();
            }
        },
        
        /**
         * 네비게이션 관련 이벤트 바인딩
         */
        bindEvents() {
            const { mobileToggle, mobileNavClose, mobileOverlay, mobileNavLinks } = WagusenApp.elements;
            
            // 햄버거 메뉴 버튼
            if (mobileToggle) {
                mobileToggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggle();
                });
            }
            
            // 닫기 버튼
            if (mobileNavClose) {
                mobileNavClose.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.close();
                });
            }
            
            // 오버레이 클릭
            if (mobileOverlay) {
                mobileOverlay.addEventListener('click', () => {
                    this.close();
                });
            }
            
            // 메뉴 링크 클릭 시 자동 닫기
            if (mobileNavLinks) {
                mobileNavLinks.forEach(link => {
                    link.addEventListener('click', () => {
                        if (WagusenApp.state.isMobileMenuOpen) {
                            setTimeout(() => this.close(), 150);
                        }
                    });
                });
            }
            
            // ESC 키로 메뉴 닫기
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && WagusenApp.state.isMobileMenuOpen) {
                    this.close();
                }
            });
            
            // 화면 크기 변경 시 메뉴 닫기
            window.addEventListener('resize', WagusenApp.debounce(() => {
                if (window.innerWidth > WagusenApp.config.breakpoints.mobile && WagusenApp.state.isMobileMenuOpen) {
                    this.close();
                }
            }, 250));
        }
    },
    
    /**
     * 스크롤 효과 관리 모듈
     * 헤더 숨김/표시와 관련된 기능을 담당
     */
    scroll: {
        /**
         * 스크롤 효과 초기화
         */
        init() {
            if (!WagusenApp.elements.header) return;
            
            this.bindEvents();
        },
        
        /**
         * 스크롤 이벤트 처리
         * 스크롤 방향에 따라 헤더를 숨기거나 표시
         */
        handleScroll() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const { hideHeaderThreshold } = WagusenApp.config.scroll;
            
            if (scrollTop > WagusenApp.state.lastScrollTop && scrollTop > hideHeaderThreshold) {
                // 아래로 스크롤 - 헤더 숨기기
                WagusenApp.elements.header.classList.add('header-hidden');
            } else {
                // 위로 스크롤 - 헤더 보이기
                WagusenApp.elements.header.classList.remove('header-hidden');
            }
            
            WagusenApp.state.lastScrollTop = Math.max(scrollTop, 0); // iOS 사파리 대응
        },
        
        /**
         * 스크롤 관련 이벤트 바인딩
         */
        bindEvents() {
            const throttledHandler = WagusenApp.throttle(
                () => this.handleScroll(), 
                WagusenApp.config.scroll.throttleDelay
            );
            
            window.addEventListener('scroll', throttledHandler, { passive: true });
        }
    },
    
    /**
     * 포스트 카드 관리 모듈
     * 포스트 카드의 클릭 이벤트와 관련된 기능을 담당
     */
    postCards: {
        /**
         * 포스트 카드 기능 초기화
         */
        init() {
            this.bindEvents();
        },
        
        /**
         * 포스트 카드 관련 이벤트 바인딩
         */
        bindEvents() {
            const postCards = document.querySelectorAll('.post-card-link');
            
            postCards.forEach(card => {
                // 카드 클릭 이벤트
                card.addEventListener('click', (e) => {
                    const href = card.getAttribute('href');
                    
                    // Ctrl/Cmd 키와 함께 클릭한 경우 새 탭에서 열기
                    if (href && !e.ctrlKey && !e.metaKey) {
                        e.preventDefault();
                        this.navigateWithTransition(href);
                    }
                });
                
                // 태그 클릭 시 이벤트 전파 방지
                const tags = card.querySelectorAll('.post-card-tag');
                tags.forEach(tag => {
                    tag.addEventListener('click', (e) => {
                        e.stopPropagation();
                    });
                });
            });
        },
        
        /**
         * 부드러운 페이지 전환 효과
         * 클릭 시 페이드 아웃 효과 후 페이지 이동
         */
        navigateWithTransition(href) {
            WagusenApp.elements.body.style.opacity = '0.8';
            WagusenApp.elements.body.style.transition = 'opacity 0.2s ease';
            
            setTimeout(() => {
                window.location.href = href;
            }, 100);
        }
    },
    
    /**
     * 전역 이벤트 바인딩
     * 앱 전체에서 사용되는 이벤트들을 등록
     */
    bindGlobalEvents() {
        // 페이지 가시성 변경 시 캐시 갱신
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshCacheIfNeeded();
            }
        });
        
        // 에러 처리
        window.addEventListener('error', (e) => {
            this.handleError(e.error, 'JavaScript 전역 에러');
        });
        
        // 처리되지 않은 Promise 에러
        window.addEventListener('unhandledrejection', (e) => {
            this.handleError(e.reason, 'Promise 에러');
        });
    },
    
    /**
     * 캐시 관리
     * 필요 시 캐시를 갱신하여 최신 상태 유지
     */
    refreshCacheIfNeeded() {
        const lastRefresh = localStorage.getItem('cacheRefresh');
        const now = Date.now();
        
        if (!lastRefresh || (now - parseInt(lastRefresh)) > this.config.cache.timeout) {
            localStorage.setItem('cacheRefresh', now.toString());
            // 실제 캐시 갱신 로직은 여기에 추가 가능
        }
    },
    
    /**
     * 디바운스 유틸리티 함수
     * 연속적인 함수 호출을 제한하여 성능 최적화
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * 스로틀 유틸리티 함수
     * 함수 호출 빈도를 제한하여 성능 최적화
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * 에러 처리
     * 애플리케이션에서 발생하는 모든 에러를 중앙에서 처리
     */
    handleError(error, context = '') {
        console.error(`와구센 앱 에러 ${context}:`, error);
        
        // 프로덕션 환경에서는 에러 리포팅 서비스로 전송 가능
        if (window.location.hostname !== 'localhost') {
            // 예: Sentry, LogRocket 등으로 에러 전송
        }
    }
};

/**
 * DOM 로드 완료 시 애플리케이션 초기화
 * 모든 DOM 요소가 준비된 후 앱을 시작
 */
document.addEventListener('DOMContentLoaded', () => {
    try {
        WagusenApp.init();
    } catch (error) {
        WagusenApp.handleError(error, 'DOMContentLoaded');
    }
});

/**
 * 전역 접근 허용 (디버깅 및 확장성을 위해)
 * 개발자 도구에서 앱 상태 확인 가능
 */
window.WagusenApp = WagusenApp;