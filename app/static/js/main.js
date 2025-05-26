// main.js - 메인 JavaScript 파일

document.addEventListener('DOMContentLoaded', function() {
    // ===== 테마 관리 =====
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
    const htmlElement = document.documentElement;
    
    // 현재 테마 상태 가져오기
    function getCurrentTheme() {
        return localStorage.getItem('theme') || 'light';
    }
    
    // 테마 적용
    function applyTheme(theme) {
        if (theme === 'dark') {
            htmlElement.classList.add('dark-theme');
        } else {
            htmlElement.classList.remove('dark-theme');
        }
        
        // 모바일 테마 스위치 상태 업데이트
        if (mobileThemeToggle) {
            const slider = mobileThemeToggle.querySelector('.theme-switch-slider');
            if (theme === 'dark') {
                slider.classList.add('active');
            } else {
                slider.classList.remove('active');
            }
        }
    }
    
    // 테마 토글 함수
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
        
        // 전구 아이콘 회전 애니메이션 추가
        if (themeToggle) {
            themeToggle.style.transform = 'scale(0.8) rotate(180deg)';
            setTimeout(() => {
                themeToggle.style.transform = '';
            }, 200);
        }
    }
    
    // 초기 테마 적용
    applyTheme(getCurrentTheme());
    
    // 테마 토글 이벤트 리스너
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', toggleTheme);
    }
    
    // ===== 모바일 메뉴 =====
    const mobileToggle = document.getElementById('mobile-toggle');
    const mobileNav = document.getElementById('mobile-nav');
    const mobileNavClose = document.getElementById('mobile-nav-close');
    const mobileOverlay = document.getElementById('mobile-overlay');
    const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
    
    function openMobileMenu() {
        mobileNav.classList.add('active');
        mobileOverlay.classList.add('active');
        mobileToggle.classList.add('active');
        document.body.classList.add('nav-open');
    }
    
    function closeMobileMenu() {
        mobileNav.classList.remove('active');
        mobileOverlay.classList.remove('active');
        mobileToggle.classList.remove('active');
        document.body.classList.remove('nav-open');
    }
    
    if (mobileToggle) {
        mobileToggle.addEventListener('click', openMobileMenu);
    }
    
    if (mobileNavClose) {
        mobileNavClose.addEventListener('click', closeMobileMenu);
    }
    
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', closeMobileMenu);
    }
    
    // 모바일 메뉴 링크 클릭 시 메뉴 닫기
    mobileNavLinks.forEach(link => {
        // 테마 토글 항목은 제외
        if (!link.querySelector('.theme-switch')) {
            link.addEventListener('click', closeMobileMenu);
        }
    });
    
    // ===== 헤더 스크롤 효과 =====
    const header = document.querySelector('.top-header');
    let lastScrollY = 0;
    let ticking = false;
    
    function updateHeader() {
        const currentScrollY = window.scrollY;
        
        // 스크롤 방향 감지
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
            // 아래로 스크롤 - 헤더 숨기기
            header.classList.add('header-hidden');
        } else {
            // 위로 스크롤 - 헤더 보이기
            header.classList.remove('header-hidden');
        }
        
        // 스크롤 위치에 따른 그림자 효과
        if (currentScrollY > 10) {
            header.classList.add('header-shadow');
        } else {
            header.classList.remove('header-shadow');
        }
        
        lastScrollY = currentScrollY;
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            window.requestAnimationFrame(updateHeader);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick);
    
    // ===== 부드러운 스크롤 =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = document.querySelector('.top-header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // ===== 백 투 톱 버튼 =====
    const backToTopButton = document.createElement('button');
    backToTopButton.className = 'back-to-top';
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.setAttribute('aria-label', '맨 위로 이동');
    document.body.appendChild(backToTopButton);
    
    // 백 투 톱 버튼 표시/숨기기
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopButton.classList.add('visible');
        } else {
            backToTopButton.classList.remove('visible');
        }
    });
    
    // 백 투 톱 버튼 클릭 이벤트
    backToTopButton.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // ===== 이미지 지연 로딩 =====
    const lazyImages = document.querySelectorAll('img[data-src]');
    
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
            rootMargin: '50px 0px'
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // IntersectionObserver를 지원하지 않는 브라우저용 폴백
        lazyImages.forEach(img => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
    
    // ===== 외부 링크 새 탭에서 열기 =====
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        if (!link.href.includes(window.location.hostname)) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
    
    // ===== 애니메이션 최적화 =====
    if ('requestIdleCallback' in window) {
        requestIdleCallback(() => {
            // 무거운 작업을 브라우저가 한가할 때 실행
            console.log('페이지 로딩 완료');
        });
    }
    
    // ===== 키보드 접근성 =====
    // Tab 키 사용 감지
    let isTabbing = false;
    
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            isTabbing = true;
            document.body.classList.add('keyboard-focus-visible');
        }
    });
    
    window.addEventListener('mousedown', () => {
        isTabbing = false;
        document.body.classList.remove('keyboard-focus-visible');
    });
    
    // ESC 키로 모바일 메뉴 닫기
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileNav.classList.contains('active')) {
            closeMobileMenu();
        }
    });
    
    // ===== 페이지 전환 효과 =====
    const pageContent = document.querySelector('main');
    if (pageContent) {
        pageContent.classList.add('page-transition', 'fade-in');
    }
    
    // ===== 스크롤 진행률 표시 =====
    const scrollProgress = document.createElement('div');
    scrollProgress.className = 'scroll-progress';
    document.body.appendChild(scrollProgress);
    
    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        scrollProgress.style.width = scrolled + '%';
    });
});

// ===== 유틸리티 함수들 =====

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 쓰로틀 함수
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 로컬 스토리지 안전하게 사용하기
function safeLocalStorage() {
    try {
        const testKey = '__test__';
        localStorage.setItem(testKey, 'test');
        localStorage.removeItem(testKey);
        return true;
    } catch (e) {
        return false;
    }
}

// 현재 페이지 하이라이트
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.desktop-nav a, .mobile-nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}