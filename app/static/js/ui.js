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
        
        if (currentScroll > lastScrollTop) {
            // 아래로 스크롤 중
            scrollUpAmount = 0;
            if (currentScroll > scrollThreshold) {
                header.classList.add('hide');
            }
        } else {
            // 위로 스크롤 중
            scrollUpAmount += (lastScrollTop - currentScroll);
            
            if (scrollUpAmount > scrollUpThreshold) {
                header.classList.remove('hide');
            }
        }
        
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    }, { passive: true }); // 성능 최적화를 위한 passive 옵션
}); 