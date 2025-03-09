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
        // 로컬 스토리지에서 테마 설정 가져오기
        const savedTheme = localStorage.getItem('theme');
        
        // 저장된 설정이 있으면 해당 설정 사용
        if (savedTheme === 'dark') {
            enableDarkMode();
        } else if (savedTheme === 'light') {
            enableLightMode();
        } else {
            // 저장된 설정이 없으면 시스템 설정 확인
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (prefersDark) {
                enableDarkMode();
            } else {
                enableLightMode();
            }
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
        
        console.log('다크 모드가 활성화되었습니다.');
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
        
        console.log('라이트 모드가 활성화되었습니다.');
    }
    
    // 테마 토글 함수
    function toggleTheme() {
        if (document.documentElement.classList.contains('dark-theme')) {
            enableLightMode();
        } else {
            enableDarkMode();
        }
    }
    
    // 시스템 테마 변경 감지 - 사용자가 직접 설정하지 않은 경우에만 시스템 설정 따름
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === null) {
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
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        const header = document.querySelector('header');
        
        if (!header) return; // null 체크 추가
        
        if (currentScroll > lastScrollTop) {
            if (currentScroll > scrollThreshold) {
                header.classList.add('hide');
            }
        } else {
            header.classList.remove('hide');
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
    
    // 슬라이더 컨트롤 값 조정 업데이트
    const gravityControl = document.getElementById('gravityControl');
    const gravityValue = document.getElementById('gravityValue');
    
    if (gravityControl && gravityValue) {
        gravityControl.addEventListener('input', function() {
            gravityValue.textContent = this.value;
        });
    }
    
    const frictionControl = document.getElementById('frictionControl');
    const frictionValue = document.getElementById('frictionValue');
    
    if (frictionControl && frictionValue) {
        frictionControl.addEventListener('input', function() {
            frictionValue.textContent = this.value;
        });
    }
});