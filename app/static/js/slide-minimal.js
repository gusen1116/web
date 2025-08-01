/**
 * 슬라이드 기능 구현
 * - 자동 슬라이드 변경
 * - 인디케이터 클릭 지원
 */
(function() {
  'use strict';

  // 슬라이드 변수 및 상수
  let currentSlide = 0;
  let slideInterval;
  const SLIDE_INTERVAL_MS = 5000; // 5초마다 슬라이드 전환
  
  // DOM 요소
  let slides;
  let indicators;

  /**
   * 슬라이드 변경 함수
   * @param {number} index - 표시할 슬라이드 인덱스
   */
  function goToSlide(index) {
      // 현재 활성 슬라이드 비활성화
      slides[currentSlide].classList.remove('active');
      indicators[currentSlide].classList.remove('active');
      
      // 새 슬라이드 활성화
      currentSlide = index;
      slides[currentSlide].classList.add('active');
      indicators[currentSlide].classList.add('active');
  }
  
  /**
   * 다음 슬라이드로 이동
   */
  function nextSlide() {
      let newIndex = currentSlide + 1;
      if (newIndex >= slides.length) {
          newIndex = 0;
      }
      goToSlide(newIndex);
  }
  
  /**
   * 슬라이드 쇼 시작
   */
  function startSlideShow() {
      clearInterval(slideInterval);
      slideInterval = setInterval(nextSlide, SLIDE_INTERVAL_MS);
  }
  
  /**
   * 슬라이드 초기화
   */
  function initSlides() {
      slides = document.querySelectorAll('.slide');
      indicators = document.querySelectorAll('.slide-indicator');
      
      if (!slides.length || !indicators.length) return;
      
      // 인디케이터 클릭 이벤트
      indicators.forEach((indicator, index) => {
          indicator.addEventListener('click', () => {
              clearInterval(slideInterval); // 자동 전환 중지
              goToSlide(index);
              startSlideShow(); // 자동 전환 재시작
          });
      });
      
      // 초기화 및 자동 슬라이드 시작
      startSlideShow();
  }
  
  // DOM 로드 완료 시 초기화
  document.addEventListener('DOMContentLoaded', initSlides);
})();