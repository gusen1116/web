// app/static/js/ui.js
document.addEventListener('DOMContentLoaded', function() {
    // 테마 토글 기능 구현
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const lightbulbIcon = themeToggle.querySelector('i');
        
        // 전구 아이콘 업데이트 함수
        function updateLightbulbIcon() {
            if (document.body.classList.contains('dark-theme')) {
                // 다크 모드 - 꺼진 전구
                lightbulbIcon.className = 'far fa-lightbulb';
                themeToggle.title = '라이트 모드로 전환';
                themeToggle.setAttribute('aria-label', '라이트 모드로 전환');
            } else {
                // 라이트 모드 - 켜진 전구
                lightbulbIcon.className = 'fas fa-lightbulb';
                themeToggle.title = '다크 모드로 전환';
                themeToggle.setAttribute('aria-label', '다크 모드로 전환');
            }
        }
        
        // 초기 테마 설정 확인 (이미 base.html에서 로드됨)
        // 초기 아이콘 상태 설정
        updateLightbulbIcon();
        
        // 클릭 이벤트 처리
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            
            // 로컬 스토리지에 테마 설정 저장
            if (document.body.classList.contains('dark-theme')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }
            
            updateLightbulbIcon();
        });
    }
    
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
    
    // 메인 슬라이더 초기화 (간소화된 버전)
    initMainSlider();
    
    function initMainSlider() {
        const sliderContainer = document.querySelector('.slider-container');
        if (!sliderContainer) return;
        
        const sliderWrapper = sliderContainer.querySelector('.slider-wrapper');
        const slides = sliderContainer.querySelectorAll('.slide');
        if (!sliderWrapper || slides.length === 0) return;
        
        let currentSlide = 0;
        let slideInterval;
        
        // 첫 번째 슬라이드 활성화
        slides[0].classList.add('active');
        
        // 자동 슬라이드 시작
        startSlideShow();
        
        function startSlideShow() {
            slideInterval = setInterval(() => {
                goToNextSlide();
            }, 5000); // 5초마다 슬라이드 변경
        }
        
        function goToNextSlide() {
            slides[currentSlide].classList.remove('active');
            currentSlide = (currentSlide + 1) % slides.length;
            slides[currentSlide].classList.add('active');
            updateSliderPosition();
        }
        
        function updateSliderPosition() {
            sliderWrapper.style.transform = `translateX(-${currentSlide * 100 / slides.length}%)`;
        }
        
        // 마우스 오버 시 자동 재생 일시 정지
        sliderContainer.addEventListener('mouseenter', () => {
            clearInterval(slideInterval);
        });
        
        sliderContainer.addEventListener('mouseleave', () => {
            startSlideShow();
        });
    }
});