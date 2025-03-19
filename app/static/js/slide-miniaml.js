/**
 * 최소한의 슬라이드 JS 파일
 * CSS 애니메이션 기반이며 JS는 인디케이터 클릭용으로만 사용
 */
document.addEventListener('DOMContentLoaded', function() {
    const slideContainer = document.querySelector('.slide-container');
    
    if (!slideContainer) return;
    
    const slides = slideContainer.querySelectorAll('.slide');
    const indicators = slideContainer.querySelectorAll('.slide-indicator');
    
    // 인디케이터 클릭 이벤트
    indicators.forEach((indicator, index) => {
      indicator.addEventListener('click', () => {
        // 모든 슬라이드 및 인디케이터 비활성화
        slides.forEach(slide => slide.classList.remove('active'));
        indicators.forEach(ind => ind.classList.remove('active'));
        
        // 선택한 슬라이드 및 인디케이터 활성화
        slides[index].classList.add('active');
        indicator.classList.add('active');
      });
    });
  });