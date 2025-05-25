// main.js - 통합된 메인 스크립트 (모바일 메뉴 + 테마 + 공통 기능)

const App = {
    // 설정 객체 (하드코딩 제거)
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
        }
    },
    
    // 상태 관리
    state: {
        isMobileMenuOpen: false,
        currentTheme: localStorage.getItem('theme') || 'auto',
        scrollPosition: 0
    },
    
    // 초기화
    init() {
        this.initTheme();
        this.initMobileMenu();
        this.initScrollEffects();
        this.initPostCards();
        this.bindEvents();
        console.log('와구센 블로그 초기화 완료');
    },
    
    // 테마 관리
    initTheme() {
        const savedTheme = this.state.currentTheme;
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (savedTheme === 'auto' && prefersDark)) {
            document.documentElement.classList.add('dark-theme');
            document.body.classList.add('dark-theme');
        }
        
        this.updateThemeUI();
    },
    
    toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark-theme');
        const newTheme = isDark ? 'light' : 'dark';
        
        document.documentElement.classList.toggle('dark-theme', !isDark);
        document.body.classList.toggle('dark-theme', !isDark);
        
        localStorage.setItem('theme', newTheme);
        this.state.currentTheme = newTheme;
        this.updateThemeUI();
        
        // 강제 리플로우
        document.body.offsetHeight;
    },
    
    updateThemeUI() {
        const isDark = document.documentElement.classList.contains('dark-theme');
        const themeText = document.querySelector('.theme-text');
        const themeSwitch = document.querySelector('.theme-switch-slider');
        
        if (themeText) {
            themeText.textContent = isDark ? '다크모드' : '라이트모드';
        }
        if (themeSwitch) {
            themeSwitch.classList.toggle('active', isDark);
        }
    },
    
    // 모바일 메뉴 관리
    initMobileMenu() {
        this.mobileElements = {
            toggle: document.getElementById('mobileToggle'),
            nav: document.getElementById('mobileNav'),
            close: document.getElementById('mobileNavClose'),
            overlay: document.getElementById('mobileOverlay'),
            links: document.querySelectorAll('.mobile-nav-link:not(.mobile-theme-toggle)')
        };
        
        if (!this.mobileElements.toggle) return;
        
        // 이벤트 리스너 등록
        this.mobileElements.toggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleMobileMenu();
        });
        
        if (this.mobileElements.close) {
            this.mobileElements.close.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeMobileMenu();
            });
        }
        
        if (this.mobileElements.overlay) {
            this.mobileElements.overlay.addEventListener('click', (e) => {
                e.preventDefault();
                this.closeMobileMenu();
            });
        }
        
        // 메뉴 링크 클릭 시 자동 닫기
        this.mobileElements.links.forEach(link => {
            link.addEventListener('click', () => {
                if (this.state.isMobileMenuOpen) {
                    setTimeout(() => this.closeMobileMenu(), 150);
                }
            });
        });
        
        // ESC 키로 메뉴 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.state.isMobileMenuOpen) {
                this.closeMobileMenu();
            }
        });
        
        // 화면 크기 변경 시 메뉴 닫기
        window.addEventListener('resize', this.debounce(() => {
            if (window.innerWidth > this.config.breakpoints.mobile && this.state.isMobileMenuOpen) {
                this.closeMobileMenu();
            }
        }, 250));
    },
    
    toggleMobileMenu() {
        if (this.state.isMobileMenuOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    },
    
    openMobileMenu() {
        this.state.isMobileMenuOpen = true;
        
        // 클래스 추가
        Object.values(this.mobileElements).forEach(el => {
            if (el && el.classList) {
                el.classList.add('active');
            }
        });
        
        // 스크롤 차단
        this.state.scrollPosition = window.scrollY;
        document.body.style.cssText = `
            overflow: hidden;
            position: fixed;
            top: -${this.state.scrollPosition}px;
            width: 100%;
        `;
        document.body.classList.add('nav-open');
        
        // 포커스 관리
        setTimeout(() => {
            if (this.mobileElements.close) {
                this.mobileElements.close.focus();
            }
        }, this.config.animation.duration);
    },
    
    closeMobileMenu() {
        this.state.isMobileMenuOpen = false;
        
        // 클래스 제거
        Object.values(this.mobileElements).forEach(el => {
            if (el && el.classList) {
                el.classList.remove('active');
            }
        });
        
        // 스크롤 복원
        document.body.style.cssText = '';
        document.body.classList.remove('nav-open');
        window.scrollTo(0, this.state.scrollPosition);
    },
    
    // 스크롤 효과
    initScrollEffects() {
        const header = document.getElementById('siteHeader');
        if (!header) return;
        
        let lastScrollTop = 0;
        let isScrolling = false;
        
        const handleScroll = this.throttle(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // 아래로 스크롤
                header.classList.add('header-hidden');
            } else {
                // 위로 스크롤
                header.classList.remove('header-hidden');
            }
            
            lastScrollTop = scrollTop;
        }, 16); // ~60fps
        
        window.addEventListener('scroll', handleScroll, { passive: true });
    },
    
    // 포스트 카드 기능
    initPostCards() {
        const postCards = document.querySelectorAll('.post-card-link');
        
        postCards.forEach(card => {
            // 클릭 이벤트
            card.addEventListener('click', (e) => {
                const href = card.getAttribute('href');
                if (href && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    this.navigateWithTransition(href);
                }
            });
            
            // 태그 클릭 이벤트 전파 방지
            const tags = card.querySelectorAll('.post-card-tag');
            tags.forEach(tag => {
                tag.addEventListener('click', (e) => {
                    e.stopPropagation();
                });
            });
        });
    },
    
    // 이벤트 바인딩
    bindEvents() {
        // 테마 토글 버튼들
        const desktopThemeToggle = document.getElementById('themeToggle');
        const mobileThemeToggle = document.getElementById('mobileThemeToggle');
        
        if (desktopThemeToggle) {
            desktopThemeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleTheme();
                
                // 시각적 피드백
                mobileThemeToggle.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    mobileThemeToggle.style.transform = '';
                }, 150);
            });
        }
        
        // 페이지 가시성 변경 시 캐시 갱신
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshCacheIfNeeded();
            }
        });
    },
    
    // 페이지 전환 (부드러운 효과)
    navigateWithTransition(href) {
        // 간단한 페이드 효과
        document.body.style.opacity = '0.8';
        document.body.style.transition = 'opacity 0.2s ease';
        
        setTimeout(() => {
            window.location.href = href;
        }, 100);
    },
    
    // 캐시 관리
    refreshCacheIfNeeded() {
        const lastRefresh = localStorage.getItem('cacheRefresh');
        const now = Date.now();
        
        if (!lastRefresh || (now - parseInt(lastRefresh)) > this.config.cache.timeout) {
            // 캐시 갱신이 필요한 경우 페이지 새로고침
            localStorage.setItem('cacheRefresh', now.toString());
        }
    },
    
    // 유틸리티 함수들
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 에러 처리
    handleError(error, context = '') {
        console.error(`앱 에러 ${context}:`, error);
        // 프로덕션에서는 에러 리포팅 서비스로 전송
    }
};

// DOM 로드 완료 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    try {
        App.init();
    } catch (error) {
        App.handleError(error, '초기화');
    }
});

// 전역 접근 허용 (디버깅용)
window.App = App;