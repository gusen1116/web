/**
 * 슬라이드 JS 파일 - 겹침 문제 해결
 */
document.addEventListener('DOMContentLoaded', function() {
  const slideContainer = document.querySelector('.slide-container');
  
  if (!slideContainer) return;
  
  const slides = slideContainer.querySelectorAll('.slide');
  const indicators = slideContainer.querySelectorAll('.slide-indicator');
  let currentSlide = 0;
  let slideInterval;
  
  // 초기 슬라이드 설정 - 모든 슬라이드 숨김 처리 후 첫 번째만 표시
  function initSlides() {
    slides.forEach((slide, index) => {
      slide.classList.remove('active');
      if (index === 0) {
        slide.classList.add('active');
      }
    });
    
    indicators.forEach((indicator, index) => {
      indicator.classList.remove('active');
      if (index === 0) {
        indicator.classList.add('active');
      }
    });
  }
  
  // 슬라이드 변경 함수
  function goToSlide(index) {
    // 자동 슬라이드 일시 중지
    if (slideInterval) {
      clearInterval(slideInterval);
    }
    
    // 모든 슬라이드 및 인디케이터 비활성화
    slides.forEach(slide => slide.classList.remove('active'));
    indicators.forEach(ind => ind.classList.remove('active'));
    
    // 선택한 슬라이드 및 인디케이터 활성화
    currentSlide = index;
    slides[currentSlide].classList.add('active');
    indicators[currentSlide].classList.add('active');
    
    // 자동 슬라이드 재시작
    startAutoSlide();
  }
  
  // 다음 슬라이드로 이동
  function nextSlide() {
    let next = currentSlide + 1;
    if (next >= slides.length) {
      next = 0;
    }
    goToSlide(next);
  }
  
  // 이전 슬라이드로 이동
  function prevSlide() {
    let prev = currentSlide - 1;
    if (prev < 0) {
      prev = slides.length - 1;
    }
    goToSlide(prev);
  }
  
  // 자동 슬라이드 시작
  function startAutoSlide() {
    if (slideInterval) {
      clearInterval(slideInterval);
    }
    slideInterval = setInterval(nextSlide, 5000);
  }
  
  // 인디케이터 클릭 이벤트
  indicators.forEach((indicator, index) => {
    indicator.addEventListener('click', () => {
      goToSlide(index);
    });
  });
  
  // 슬라이드 컨테이너에 마우스 오버시 자동 슬라이드 일시 중지
  slideContainer.addEventListener('mouseenter', () => {
    if (slideInterval) {
      clearInterval(slideInterval);
    }
  });
  
  // 슬라이드 컨테이너에서 마우스 아웃시 자동 슬라이드 재시작
  slideContainer.addEventListener('mouseleave', () => {
    startAutoSlide();
  });
  
  // 슬라이드 초기화 및 자동 슬라이드 시작
  initSlides();
  startAutoSlide();
});