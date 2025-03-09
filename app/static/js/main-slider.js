/**
 * main-slider.js - 메인 페이지 배너 슬라이더 스크립트
 * 이 파일은 홈페이지의 배너 슬라이더를 부드럽게 작동시키는 기능을 제공합니다.
 */

document.addEventListener('DOMContentLoaded', function() {
    // 슬라이더 요소들 참조
    const sliderContainer = document.querySelector('.slider-container');
    if (!sliderContainer) return; // 슬라이더가 없으면 종료
    
    const sliderWrapper = document.querySelector('.slider-wrapper');
    const slides = document.querySelectorAll('.slide');
    const indicatorsContainer = document.querySelector('.slider-indicators');
    
    // 슬라이더 관련 변수
    let currentIndex = 0;
    let autoSlideInterval;
    let isTransitioning = false;
    const slideInterval = 5000; // 5초
    
    // 터치 이벤트 변수
    let touchStartX = 0;
    let touchEndX = 0;
    
    // 슬라이더가 정의되어 있고 슬라이드가 있는지 확인
    if (!sliderWrapper || !slides.length) {
        console.log('슬라이더 요소가 없거나 슬라이드가 없습니다.');
        return;
    }
    
    // 슬라이더 초기 설정
    function initSlider() {
        console.log('슬라이더 초기화 중...');
        
        // 슬라이더 스타일 설정
        sliderWrapper.style.display = 'flex';
        sliderWrapper.style.width = `${slides.length * 100}%`;
        sliderWrapper.style.transition = 'transform 0.5s ease-in-out';
        
        // 각 슬라이드 스타일 설정
        slides.forEach(slide => {
            slide.style.flex = `0 0 ${100 / slides.length}%`;
        });
        
        // 첫 번째 슬라이드 활성화
        slides[0].classList.add('active');
        
        // 인디케이터 생성
        createIndicators();
        
        // 첫 번째 인디케이터 활성화
        updateIndicators();
        
        // 자동 슬라이드 시작
        startAutoSlide();
        
        // 이벤트 리스너 설정
        setupEventListeners();
        
        console.log('슬라이더 초기화 완료');
    }
    
    // 인디케이터 생성 함수
    function createIndicators() {
        // 인디케이터 컨테이너가 없으면 생성
        if (!indicatorsContainer) {
            const newIndicatorsContainer = document.createElement('div');
            newIndicatorsContainer.className = 'slider-indicators';
            sliderContainer.appendChild(newIndicatorsContainer);
            indicatorsContainer = newIndicatorsContainer;
        } else {
            // 기존 인디케이터 컨테이너가 있으면 비우기
            indicatorsContainer.innerHTML = '';
        }
        
        // 각 슬라이드에 대한 인디케이터 생성
        slides.forEach((_, index) => {
            const indicator = document.createElement('span');
            indicator.className = 'indicator';
            indicator.dataset.index = index;
            indicator.addEventListener('click', () => goToSlide(index));
            indicatorsContainer.appendChild(indicator);
        });
    }
    
    // 인디케이터 업데이트 함수
    function updateIndicators() {
        const indicators = document.querySelectorAll('.indicator');
        indicators.forEach((indicator, index) => {
            if (index === currentIndex) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }
    
    // 특정 슬라이드로 이동하는 함수
    function goToSlide(index) {
        // 이미 전환 중이면 무시
        if (isTransitioning) return;
        
        // 슬라이드 인덱스 보정
        if (index < 0) index = slides.length - 1;
        if (index >= slides.length) index = 0;
        
        // 현재 인덱스 업데이트
        currentIndex = index;
        
        // 슬라이드 전환
        const offset = -currentIndex * (100 / slides.length);
        sliderWrapper.style.transform = `translateX(${offset}%)`;
        
        // 전환 중 상태 설정 및 이전 활성 슬라이드 비활성화
        isTransitioning = true;
        slides.forEach(slide => slide.classList.remove('active'));
        
        // 새 슬라이드 활성화
        setTimeout(() => {
            slides[currentIndex].classList.add('active');
            isTransitioning = false;
            updateIndicators();
        }, 500); // 전환 시간과 동일하게 설정
    }
    
    // 다음 슬라이드로 이동
    function nextSlide() {
        goToSlide(currentIndex + 1);
    }
    
    // 이전 슬라이드로 이동
    function prevSlide() {
        goToSlide(currentIndex - 1);
    }
    
    // 자동 슬라이드 시작
    function startAutoSlide() {
        // 기존 인터벌 제거
        if (autoSlideInterval) {
            clearInterval(autoSlideInterval);
        }
        
        // 새 인터벌 설정
        autoSlideInterval = setInterval(nextSlide, slideInterval);
    }
    
    // 자동 슬라이드 재시작
    function resetAutoSlide() {
        clearInterval(autoSlideInterval);
        startAutoSlide();
    }
    
    // 스와이프 처리 함수
    function handleSwipe() {
        const minSwipeDistance = 50; // 최소 스와이프 거리
        const swipeDistance = touchEndX - touchStartX;
        
        if (Math.abs(swipeDistance) < minSwipeDistance) return;
        
        if (swipeDistance < 0) {
            // 왼쪽으로 스와이프 (다음 슬라이드)
            nextSlide();
        } else {
            // 오른쪽으로 스와이프 (이전 슬라이드)
            prevSlide();
        }
        
        resetAutoSlide();
    }
    
    // 내비게이션 버튼 생성
    function createNavigationButtons() {
        // 이전 버튼
        const prevButton = document.createElement('button');
        prevButton.className = 'slider-nav-btn prev-btn';
        prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevButton.setAttribute('aria-label', '이전 슬라이드');
        prevButton.addEventListener('click', () => {
            prevSlide();
            resetAutoSlide();
        });
        
        // 다음 버튼
        const nextButton = document.createElement('button');
        nextButton.className = 'slider-nav-btn next-btn';
        nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextButton.setAttribute('aria-label', '다음 슬라이드');
        nextButton.addEventListener('click', () => {
            nextSlide();
            resetAutoSlide();
        });
        
        // 버튼 컨테이너 생성 및 추가
        const navContainer = document.createElement('div');
        navContainer.className = 'slider-nav';
        navContainer.appendChild(prevButton);
        navContainer.appendChild(nextButton);
        sliderContainer.appendChild(navContainer);
    }
    
    // 이벤트 리스너 설정
    function setupEventListeners() {
        // 터치 이벤트 (모바일용)
        sliderContainer.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        sliderContainer.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
        
        // 마우스 이벤트 (데스크톱용)
        sliderContainer.addEventListener('mouseenter', () => {
            // 마우스가 슬라이더 위에 있을 때 자동 재생 중지
            clearInterval(autoSlideInterval);
        });
        
        sliderContainer.addEventListener('mouseleave', () => {
            // 마우스가 슬라이더를 벗어나면 자동 재생 시작
            startAutoSlide();
        });
        
        // 슬라이드 전환 완료 이벤트
        sliderWrapper.addEventListener('transitionend', () => {
            isTransitioning = false;
        });
        
        // 키보드 접근성
        sliderContainer.setAttribute('tabindex', '0');
        sliderContainer.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                prevSlide();
                resetAutoSlide();
            } else if (e.key === 'ArrowRight') {
                nextSlide();
                resetAutoSlide();
            }
        });
        
        // 창 크기 변경 시 슬라이더 조정
        window.addEventListener('resize', () => {
            // 현재 슬라이드로 이동 (슬라이더 위치 재조정)
            const offset = -currentIndex * (100 / slides.length);
            sliderWrapper.style.transform = `translateX(${offset}%)`;
        });
    }
    
    // 내비게이션 버튼 생성
    createNavigationButtons();
    
    // 슬라이더 초기화
    initSlider();
});