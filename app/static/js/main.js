// main.js - GitHub 스타일 최적화된 JavaScript

(function() {
    'use strict';

    // ===== 유틸리티 함수 =====
    const $ = (selector, context = document) => context.querySelector(selector);
    const $$ = (selector, context = document) => context.querySelectorAll(selector);
    
    // 디바운스 함수 (성능 최적화)
    const debounce = (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // 스로틀 함수 (성능 최적화)
    const throttle = (func, limit) => {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };

    // ===== 테마 관리 시스템 =====
    class ThemeManager {
        constructor() {
            this.theme = localStorage.getItem('theme') || 'light';
            this.init();
        }

        init() {
            // 초기 테마 적용
            this.applyTheme(this.theme);
            
            // 시스템 테마 변경 감지
            if (window.matchMedia) {
                const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
                darkModeQuery.addEventListener('change', (e) => {
                    if (!localStorage.getItem('theme')) {
                        this.applyTheme(e.matches ? 'dark' : 'light');
                    }
                });
            }
        }

        applyTheme(theme) {
            this.theme = theme;
            const isDark = theme === 'dark';
            
            document.documentElement.classList.toggle('dark-theme', isDark);
            document.body.classList.toggle('dark-theme', isDark);
            
            // 메타 테마 색상 업데이트
            const metaThemeColor = $('meta[name="theme-color"]');
            if (metaThemeColor) {
                metaThemeColor.content = isDark ? '#0d1117' : '#ffffff';
            }
            
            // 테마 스위치 상태 업데이트
            this.updateThemeSwitches(isDark);
        }

        updateThemeSwitches(isDark) {
            // 데스크톱 테마 토글 업데이트
            const desktopToggle = $('#theme-toggle');
            if (desktopToggle) {
                desktopToggle.setAttribute('aria-pressed', isDark);
                const statusText = $('#theme-status');
                if (statusText) {
                    statusText.textContent = `현재 ${isDark ? '다크' : '라이트'} 모드`;
                }
            }
            
            // 모바일 테마 토글 업데이트
            const mobileToggle = $('#mobile-theme-toggle');
            if (mobileToggle) {
                mobileToggle.setAttribute('aria-checked', isDark);
                const themeSlider = $('.theme-switch-slider', mobileToggle);
                if (themeSlider) {
                    themeSlider.classList.toggle('active', isDark);
                }
            }
        }

        toggle() {
            const newTheme = this.theme === 'dark' ? 'light' : 'dark';
            this.applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
            
            // 애니메이션 피드백
            document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        }
    }

    // ===== 모바일 네비게이션 시스템 =====
    class MobileNavigation {
        constructor() {
            this.isOpen = false;
            this.toggle = $('#mobile-toggle');
            this.nav = $('#mobile-nav');
            this.close = $('#mobile-nav-close');
            this.overlay = $('#mobile-overlay');
            this.navLinks = $$('.mobile-nav-link:not(.mobile-theme-toggle)');
            
            this.init();
        }

        init() {
            if (!this.toggle || !this.nav) return;

            // 이벤트 리스너
            this.toggle.addEventListener('click', () => this.toggleMenu());
            this.close?.addEventListener('click', () => this.closeMenu());
            this.overlay?.addEventListener('click', () => this.closeMenu());
            
            // 네비게이션 링크 클릭시 메뉴 닫기
            this.navLinks.forEach(link => {
                link.addEventListener('click', () => {
                    setTimeout(() => this.closeMenu(), 150);
                });
            });
            
            // ESC 키로 닫기
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.closeMenu();
                }
            });
            
            // 윈도우 리사이즈시 메뉴 닫기
            window.addEventListener('resize', debounce(() => {
                if (window.innerWidth > 768 && this.isOpen) {
                    this.closeMenu();
                }
            }, 250));
            
            // 스와이프 제스처
            this.initSwipeGesture();
        }

        toggleMenu() {
            this.isOpen ? this.closeMenu() : this.openMenu();
        }

        openMenu() {
            this.isOpen = true;
            
            // 스크롤 위치 저장 및 고정
            const scrollY = window.scrollY;
            document.body.style.position = 'fixed';
            document.body.style.top = `-${scrollY}px`;
            document.body.style.width = '100%';
            document.body.setAttribute('data-scroll-y', scrollY);
            
            // 클래스 추가
            this.nav.classList.add('active');
            this.toggle.classList.add('active');
            this.overlay?.classList.add('active');
            document.body.classList.add('nav-open');
            
            // ARIA 속성 업데이트
            this.toggle.setAttribute('aria-expanded', 'true');
            this.nav.setAttribute('aria-hidden', 'false');
            
            // 포커스 관리
            setTimeout(() => {
                this.close?.focus();
            }, 300);
            
            // 포커스 트랩 설정
            this.trapFocus();
        }

        closeMenu() {
            this.isOpen = false;
            
            // 클래스 제거
            this.nav.classList.remove('active');
            this.toggle.classList.remove('active');
            this.overlay?.classList.remove('active');
            document.body.classList.remove('nav-open');
            
            // 스크롤 위치 복원
            const scrollY = document.body.getAttribute('data-scroll-y');
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.width = '';
            
            if (scrollY) {
                window.scrollTo(0, parseInt(scrollY));
                document.body.removeAttribute('data-scroll-y');
            }
            
            // ARIA 속성 업데이트
            this.toggle.setAttribute('aria-expanded', 'false');
            this.nav.setAttribute('aria-hidden', 'true');
            
            // 포커스 복원
            this.toggle.focus();
            
            // 포커스 트랩 해제
            this.releaseFocus();
        }

        initSwipeGesture() {
            let touchStartX = 0;
            let touchStartY = 0;
            
            this.nav.addEventListener('touchstart', (e) => {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
            }, { passive: true });
            
            this.nav.addEventListener('touchend', (e) => {
                const touchEndX = e.changedTouches[0].clientX;
                const touchEndY = e.changedTouches[0].clientY;
                const diffX = touchStartX - touchEndX;
                const diffY = Math.abs(touchStartY - touchEndY);
                
                // 오른쪽으로 스와이프시 메뉴 닫기
                if (diffX < -50 && diffY < 100) {
                    this.closeMenu();
                }
            }, { passive: true });
        }

        trapFocus() {
            const focusableElements = this.nav.querySelectorAll(
                'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;
            
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            this.handleTabKey = (e) => {
                if (e.key !== 'Tab') return;
                
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            };
            
            document.addEventListener('keydown', this.handleTabKey);
        }

        releaseFocus() {
            if (this.handleTabKey) {
                document.removeEventListener('keydown', this.handleTabKey);
            }
        }
    }

    // ===== 헤더 스크롤 효과 =====
    class HeaderScroll {
        constructor() {
            this.header = $('.top-header');
            this.lastScrollTop = 0;
            this.scrollTimer = null;
            
            this.init();
        }

        init() {
            if (!this.header) return;

            const handleScroll = throttle(() => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                // 스크롤 방향 감지
                if (scrollTop > this.lastScrollTop && scrollTop > 100) {
                    // 아래로 스크롤 - 헤더 숨기기
                    this.header.classList.add('header-hidden');
                } else {
                    // 위로 스크롤 - 헤더 보이기
                    this.header.classList.remove('header-hidden');
                }
                
                // 스크롤 멈춤 감지
                clearTimeout(this.scrollTimer);
                this.scrollTimer = setTimeout(() => {
                    if (scrollTop < 100) {
                        this.header.classList.remove('header-hidden');
                    }
                }, 300);
                
                this.lastScrollTop = scrollTop;
            }, 100);

            window.addEventListener('scroll', handleScroll, { passive: true });
        }
    }

    // ===== 스크롤 진행률 표시기 =====
    class ScrollProgress {
        constructor() {
            this.progressBar = null;
            this.init();
        }

        init() {
            // 진행률 바 생성
            this.progressBar = document.createElement('div');
            this.progressBar.className = 'scroll-progress';
            document.body.appendChild(this.progressBar);

            // 스크롤 이벤트
            const updateProgress = throttle(() => {
                const scrolled = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
                this.progressBar.style.width = Math.min(scrolled, 100) + '%';
            }, 50);

            window.addEventListener('scroll', updateProgress, { passive: true });
        }
    }

    // ===== Back to Top 버튼 =====
    class BackToTop {
        constructor() {
            this.button = null;
            this.init();
        }

        init() {
            // 버튼 생성
            this.button = document.createElement('button');
            this.button.className = 'back-to-top';
            this.button.innerHTML = '<i class="fas fa-arrow-up" aria-hidden="true"></i>';
            this.button.setAttribute('aria-label', '맨 위로 이동');
            this.button.setAttribute('title', '맨 위로 이동');
            document.body.appendChild(this.button);

            // 클릭 이벤트
            this.button.addEventListener('click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });

            // 스크롤시 표시/숨김
            const toggleVisibility = throttle(() => {
                if (window.scrollY > 300) {
                    this.button.classList.add('visible');
                } else {
                    this.button.classList.remove('visible');
                }
            }, 200);

            window.addEventListener('scroll', toggleVisibility, { passive: true });
        }
    }

    // ===== 이미지 레이지 로딩 =====
    class LazyImageLoader {
        constructor() {
            this.images = $$('img[data-src]');
            this.init();
        }

        init() {
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            this.loadImage(img);
                            observer.unobserve(img);
                        }
                    });
                }, {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                });

                this.images.forEach(img => imageObserver.observe(img));
            } else {
                // 폴백: 모든 이미지 즉시 로드
                this.images.forEach(img => this.loadImage(img));
            }
        }

        loadImage(img) {
            const src = img.dataset.src;
            if (!src) return;

            // 이미지 프리로드
            const tempImg = new Image();
            tempImg.onload = () => {
                img.src = src;
                img.removeAttribute('data-src');
                img.classList.add('fade-in');
            };
            tempImg.onerror = () => {
                img.alt = '이미지를 불러올 수 없습니다';
                img.classList.add('error');
            };
            tempImg.src = src;
        }
    }

    // ===== 포스트 카드 향상 =====
    class PostCardEnhancer {
        constructor() {
            this.cards = $$('.post-card');
            this.init();
        }

        init() {
            this.cards.forEach(card => {
                // 터치 디바이스에서 호버 효과 개선
                card.addEventListener('touchstart', () => {
                    card.classList.add('touch-hover');
                }, { passive: true });

                card.addEventListener('touchend', () => {
                    setTimeout(() => {
                        card.classList.remove('touch-hover');
                    }, 300);
                }, { passive: true });

                // 링크 전체 영역 클릭 가능하게
                const link = card.querySelector('.post-card-link');
                if (link) {
                    card.style.cursor = 'pointer';
                    card.addEventListener('click', (e) => {
                        if (e.target.tagName !== 'A') {
                            link.click();
                        }
                    });
                }
            });
        }
    }

    // ===== 폼 검증 =====
    class FormValidator {
        constructor() {
            this.forms = $$('form[data-validate]');
            this.init();
        }

        init() {
            this.forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                    }
                });

                // 실시간 검증
                const inputs = form.querySelectorAll('input[required], textarea[required]');
                inputs.forEach(input => {
                    input.addEventListener('blur', () => {
                        this.validateField(input);
                    });
                });
            });
        }

        validateForm(form) {
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;

            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            return isValid;
        }

        validateField(field) {
            const value = field.value.trim();
            const type = field.type;
            let isValid = true;

            // 빈 값 체크
            if (!value) {
                this.showError(field, '이 필드는 필수입니다.');
                return false;
            }

            // 이메일 검증
            if (type === 'email' && !this.isValidEmail(value)) {
                this.showError(field, '올바른 이메일 주소를 입력해주세요.');
                return false;
            }

            // 전화번호 검증
            if (type === 'tel' && !this.isValidPhone(value)) {
                this.showError(field, '올바른 전화번호를 입력해주세요.');
                return false;
            }

            if (isValid) {
                this.clearError(field);
            }

            return isValid;
        }

        isValidEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        }

        isValidPhone(phone) {
            return /^[\d\s\-\+\(\)]+$/.test(phone);
        }

        showError(field, message) {
            field.classList.add('error');
            
            let errorEl = field.nextElementSibling;
            if (!errorEl || !errorEl.classList.contains('form-error')) {
                errorEl = document.createElement('span');
                errorEl.className = 'form-error';
                field.parentNode.insertBefore(errorEl, field.nextSibling);
            }
            errorEl.textContent = message;
        }

        clearError(field) {
            field.classList.remove('error');
            
            const errorEl = field.nextElementSibling;
            if (errorEl && errorEl.classList.contains('form-error')) {
                errorEl.remove();
            }
        }
    }

    // ===== 성능 모니터링 (개발용) =====
    class PerformanceMonitor {
        constructor() {
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                this.init();
            }
        }

        init() {
            // 페이지 로드 시간
            window.addEventListener('load', () => {
                const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                console.log(`Page load time: ${loadTime}ms`);
            });

            // FPS 모니터링
            let lastTime = performance.now();
            let frames = 0;
            
            const measureFPS = () => {
                frames++;
                const currentTime = performance.now();
                
                if (currentTime >= lastTime + 1000) {
                    const fps = Math.round((frames * 1000) / (currentTime - lastTime));
                    if (fps < 30) {
                        console.warn(`Low FPS detected: ${fps}`);
                    }
                    frames = 0;
                    lastTime = currentTime;
                }
                
                requestAnimationFrame(measureFPS);
            };
            
            // requestAnimationFrame(measureFPS);
        }
    }

    // ===== 초기화 =====
    document.addEventListener('DOMContentLoaded', () => {
        // 핵심 기능 초기화
        const themeManager = new ThemeManager();
        const mobileNav = new MobileNavigation();
        const headerScroll = new HeaderScroll();
        
        // 부가 기능 초기화 (지연 로드)
        requestIdleCallback(() => {
            new ScrollProgress();
            new BackToTop();
            new LazyImageLoader();
            new PostCardEnhancer();
            new FormValidator();
            new PerformanceMonitor();
        }, { timeout: 2000 });

        // 테마 토글 이벤트
        const themeToggle = $('#theme-toggle');
        const mobileThemeToggle = $('#mobile-theme-toggle');
        
        themeToggle?.addEventListener('click', () => themeManager.toggle());
        mobileThemeToggle?.addEventListener('click', () => themeManager.toggle());

        // 전역 에러 핸들링
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
        });

        // 서비스 워커 등록 (PWA)
        if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
            navigator.serviceWorker.register('/sw.js').catch(err => {
                console.error('Service Worker registration failed:', err);
            });
        }
    });

    // requestIdleCallback 폴리필
    window.requestIdleCallback = window.requestIdleCallback || function(handler) {
        const startTime = Date.now();
        return setTimeout(() => {
            handler({
                didTimeout: false,
                timeRemaining: () => Math.max(0, 50.0 - (Date.now() - startTime))
            });
        }, 1);
    };

})();