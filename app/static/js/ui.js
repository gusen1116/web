// app/static/js/ui.js
document.addEventListener('DOMContentLoaded', function() {
    // 테마 토글 기능 구현
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        // 초기 테마 설정 확인
        checkTheme();
        
        // 클릭 이벤트 처리
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }
    
    // 테마 확인 및 적용 함수
    function checkTheme() {
        // 사용자 선호 테마 확인 (시스템 설정)
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // 로컬 스토리지에서 테마 설정 가져오기
        const savedTheme = localStorage.getItem('theme');
        
        // 먼저 저장된 설정 확인, 없으면 시스템 설정 사용
        if (savedTheme === 'dark' || (savedTheme === null && prefersDark)) {
            enableDarkMode();
        } else {
            enableLightMode();
        }
    }
    
    // 다크 모드 활성화
    function enableDarkMode() {
        document.documentElement.classList.add('dark-theme');
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        
        // 테마 토글 버튼 접근성 레이블 업데이트
        if (themeToggle) {
            themeToggle.setAttribute('aria-label', '라이트 모드로 전환');
            themeToggle.title = '라이트 모드로 전환';
        }
    }
    
    // 라이트 모드 활성화
    function enableLightMode() {
        document.documentElement.classList.remove('dark-theme');
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        
        // 테마 토글 버튼 접근성 레이블 업데이트
        if (themeToggle) {
            themeToggle.setAttribute('aria-label', '다크 모드로 전환');
            themeToggle.title = '다크 모드로 전환';
        }
    }
    
    // 테마 토글 함수
    function toggleTheme() {
        if (document.documentElement.classList.contains('dark-theme')) {
            enableLightMode();
        } else {
            enableDarkMode();
        }
    }
    
    // 시스템 테마 변경 감지
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (localStorage.getItem('theme') === null) {
            // 사용자가 직접 설정하지 않은 경우에만 시스템 설정 따름
            if (e.matches) {
                enableDarkMode();
            } else {
                enableLightMode();
            }
        }
    });
    
    // 스크롤 시 헤더 숨김/표시 효과
    let lastScrollTop = 0;
    const scrollThreshold = 50;
    const scrollUpThreshold = 20; // 빠르게 감지하도록 임계값 설정
    let scrollUpAmount = 0;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        const header = document.querySelector('header');
        
        if (!header) return; // null 체크 추가
        
        if (currentScroll > lastScrollTop) {
            scrollUpAmount = 0;
            if (currentScroll > scrollThreshold) {
                header.classList.add('hide');
            }
        } else {
            scrollUpAmount += (lastScrollTop - currentScroll);
            
            if (scrollUpAmount > scrollUpThreshold) {
                header.classList.remove('hide');
            }
        }
        
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    }, { passive: true });
    
    // 애니메이션 효과
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('visible');
        }, 100 * index);
    });
    
    // 슬라이더 초기화
    initSlider();
});

// 슬라이더 초기화 함수
function initSlider() {
    // 슬라이더 요소들
    const sliderContainer = document.querySelector('.slider-container');
    if (!sliderContainer) return;
    
    const sliderWrapper = sliderContainer.querySelector('.slider-wrapper');
    const slides = sliderContainer.querySelectorAll('.slide');
    const indicatorsContainer = sliderContainer.querySelector('.slider-indicators');
    const prevBtn = sliderContainer.querySelector('.prev-btn');
    const nextBtn = sliderContainer.querySelector('.next-btn');
    
    if (!slides.length || !sliderWrapper) return;
    
    // 인디케이터 생성
    if (indicatorsContainer) {
        slides.forEach((_, index) => {
            const indicator = document.createElement('span');
            indicator.classList.add('indicator');
            if (index === 0) indicator.classList.add('active');
            indicator.dataset.index = index;
            indicator.addEventListener('click', () => goToSlide(index));
            indicatorsContainer.appendChild(indicator);
        });
    }
    
    // 변수 선언
    let currentIndex = 0;
    let interval;
    
    // 첫 번째 슬라이드 활성화
    slides[0].classList.add('active');
    
    // 슬라이드 전환 함수
    function goToSlide(index) {
        if (index < 0) index = slides.length - 1;
        if (index >= slides.length) index = 0;
        
        slides[currentIndex].classList.remove('active');
        currentIndex = index;
        slides[currentIndex].classList.add('active');
        
        const offset = -currentIndex * (100 / slides.length);
        sliderWrapper.style.transform = `translateX(${offset}%)`;
        
        // 인디케이터 업데이트
        if (indicatorsContainer) {
            indicatorsContainer.querySelectorAll('.indicator').forEach((ind, i) => {
                if (i === currentIndex) ind.classList.add('active');
                else ind.classList.remove('active');
            });
        }
    }
    
    // 자동 슬라이드
    function startAutoSlide() {
        interval = setInterval(() => {
            goToSlide(currentIndex + 1);
        }, 5000); // 5초마다 전환
    }
    
    // 터치/스와이프 처리
    let touchStartX = 0;
    let touchEndX = 0;
    
    sliderContainer.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
        clearInterval(interval); // 터치 시작 시 자동 슬라이드 중지
    }, { passive: true });
    
    sliderContainer.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
        startAutoSlide(); // 터치 종료 시 자동 슬라이드 재시작
    }, { passive: true });
    
    function handleSwipe() {
        const swipeThreshold = 50; // 최소 스와이프 거리
        
        if (touchEndX < touchStartX - swipeThreshold) {
            // 왼쪽으로 스와이프 (다음 슬라이드)
            goToSlide(currentIndex + 1);
        } else if (touchEndX > touchStartX + swipeThreshold) {
            // 오른쪽으로 스와이프 (이전 슬라이드)
            goToSlide(currentIndex - 1);
        }
    }
    
    // 네비게이션 버튼 이벤트
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            goToSlide(currentIndex - 1);
            clearInterval(interval);
            startAutoSlide();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            goToSlide(currentIndex + 1);
            clearInterval(interval);
            startAutoSlide();
        });
    }
    
    // 마우스 오버 시 자동 슬라이드 일시 중지
    sliderContainer.addEventListener('mouseenter', () => {
        clearInterval(interval);
    });
    
    sliderContainer.addEventListener('mouseleave', () => {
        startAutoSlide();
    });
    
    // 시작 시 자동 슬라이드 실행
    startAutoSlide();
}