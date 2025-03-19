/**
 * app.js - 통합 JavaScript 파일
 * 모든 기능을 하나의 파일로 통합하여 관리 용이성 개선
 */

document.addEventListener('DOMContentLoaded', function() {
    // 테마 토글 기능
    initThemeToggle();
    
    // 모바일 메뉴 토글
    initMobileMenu();
    
    // 스크롤 시 헤더 숨김/표시 효과
    initScrollHeader();
    
    // 애니메이션 효과
    initAnimations();
    
    // 슬라이드 기능 초기화
    initSlides();
    
    // 시뮬레이션 초기화 (해당 페이지에 있을 경우)
    if (document.getElementById('simulationCanvas')) {
        initSimulation();
    }
});

// 테마 토글 기능
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    themeToggle.addEventListener('click', function() {
        const isDark = document.documentElement.classList.contains('dark-theme');
        
        if (isDark) {
            document.documentElement.classList.remove('dark-theme');
            document.body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
            themeToggle.setAttribute('aria-label', '다크 모드로 전환');
        } else {
            document.documentElement.classList.add('dark-theme');
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
            themeToggle.setAttribute('aria-label', '라이트 모드로 전환');
        }
    });
}

// 모바일 메뉴 토글
function initMobileMenu() {
    const mobileToggle = document.querySelector('.mobile-toggle');
    if (!mobileToggle) return;
    
    mobileToggle.addEventListener('click', function() {
        const mainNav = document.querySelector('.main-nav ul');
        
        mainNav.classList.toggle('active');
        
        const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
        mobileToggle.setAttribute('aria-expanded', !isExpanded);
        mobileToggle.setAttribute('aria-label', isExpanded ? '메뉴 열기' : '메뉴 닫기');
        mobileToggle.innerHTML = isExpanded ? '<i class="fas fa-bars"></i>' : '<i class="fas fa-times"></i>';
    });
}

// 스크롤 시 헤더 숨김/표시 효과
function initScrollHeader() {
    let lastScrollTop = 0;
    const scrollThreshold = 50;
    const topHeader = document.querySelector('.top-header');
    const mainNav = document.querySelector('.main-nav');
    
    if (!topHeader || !mainNav) return;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
        if (currentScroll > lastScrollTop && currentScroll > scrollThreshold) {
            topHeader.style.transform = 'translateY(-100%)';
            mainNav.style.transform = 'translateY(-100%)';
        } else {
            topHeader.style.transform = 'translateY(0)';
            mainNav.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    }, { passive: true });
}

// 애니메이션 효과
function initAnimations() {
    const fadeElements = document.querySelectorAll('.fade-in');
    
    if (fadeElements.length === 0) return;
    
    // 관찰자 옵션 설정
    const options = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    // 요소가 보이면 'visible' 클래스 추가
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, options);
    
    // 각 애니메이션 요소 관찰 시작
    fadeElements.forEach((el, index) => {
        el.style.transitionDelay = `${index * 100}ms`;
        observer.observe(el);
    });
}

// 슬라이드 기능 초기화
function initSlides() {
    const slides = document.getElementById('slides');
    if (slides) {
        slides.classList.add('active');
    } 
    const dots = document.querySelectorAll('.slide-dot');
    const prevBtn = document.getElementById('slide-prev');
    const nextBtn = document.getElementById('slide-next');
    
    if (!slides) return;
    
    let currentSlide = 0;
    const totalSlides = dots.length;
    
    // 슬라이드 변경 함수
    function goToSlide(index) {
        currentSlide = index;
        slides.style.transform = `translateX(-${currentSlide * 100}%)`;
        
        // 활성 도트 업데이트
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentSlide);
        });
    }
    
    // 다음 슬라이드
    function nextSlide() {
        goToSlide((currentSlide + 1) % totalSlides);
    }
    
    // 이전 슬라이드
    function prevSlide() {
        goToSlide((currentSlide - 1 + totalSlides) % totalSlides);
    }
    
    // 버튼 이벤트 리스너
    if (prevBtn) prevBtn.addEventListener('click', prevSlide);
    if (nextBtn) nextBtn.addEventListener('click', nextSlide);
    
    // 도트 이벤트 리스너
    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            goToSlide(parseInt(dot.dataset.index));
        });
    });
    
    // 자동 슬라이드
    let slideInterval = setInterval(nextSlide, 5000);
    
    // 마우스 오버시 자동 슬라이드 중지
    const slideContainer = document.querySelector('.slide-container');
    if (slideContainer) {
        slideContainer.addEventListener('mouseenter', () => {
            clearInterval(slideInterval);
        });
        
        slideContainer.addEventListener('mouseleave', () => {
            slideInterval = setInterval(nextSlide, 5000);
        });
    }
}

// 시뮬레이션 초기화
function initSimulation() {
    const canvas = document.getElementById('simulationCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 캔버스 크기 설정
    function resizeCanvas() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 시뮬레이션 객체 및 설정
    const simulation = {
        particles: [],
        gravity: 9.8,
        friction: 0.01,
        running: false
    };
    
    // 시뮬레이션 초기화
    function initSimulationState() {
        // 초기 입자 생성
        simulation.particles = [];
        for (let i = 0; i < 20; i++) {
            simulation.particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: Math.random() * 2 - 1,
                vy: Math.random() * 2 - 1,
                radius: 5 + Math.random() * 10
            });
        }
    }
    
    // 물리 법칙 적용 및 렌더링
    function updateSimulation() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        for (const particle of simulation.particles) {
            // 물리 법칙 적용
            particle.vy += simulation.gravity * 0.01;
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // 벽 충돌 처리
            if (particle.x < particle.radius) {
                particle.x = particle.radius;
                particle.vx *= -0.8;
            }
            if (particle.x > canvas.width - particle.radius) {
                particle.x = canvas.width - particle.radius;
                particle.vx *= -0.8;
            }
            if (particle.y < particle.radius) {
                particle.y = particle.radius;
                particle.vy *= -0.8;
            }
            if (particle.y > canvas.height - particle.radius) {
                particle.y = canvas.height - particle.radius;
                particle.vy *= -0.8;
            }
            
            // 입자 그리기
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#0366d6';
            ctx.fill();
        }
        
        if (simulation.running) {
            requestAnimationFrame(updateSimulation);
        }
    }
    
    // 시뮬레이션 제어 버튼
    const startButton = document.getElementById('startSimulation');
    const stopButton = document.getElementById('stopSimulation');
    const resetButton = document.getElementById('resetSimulation');
    
    if (startButton) {
        startButton.addEventListener('click', function() {
            simulation.running = true;
            updateSimulation();
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', function() {
            simulation.running = false;
        });
    }
    
    if (resetButton) {
        resetButton.addEventListener('click', function() {
            initSimulationState();
            if (!simulation.running) {
                updateSimulation();
            }
        });
    }
    
    // 매개변수 조정
    const gravityControl = document.getElementById('gravityControl');
    if (gravityControl) {
        gravityControl.addEventListener('input', function(e) {
            simulation.gravity = parseFloat(e.target.value);
            document.getElementById('gravityValue').textContent = e.target.value;
        });
    }
    
    const frictionControl = document.getElementById('frictionControl');
    if (frictionControl) {
        frictionControl.addEventListener('input', function(e) {
            simulation.friction = parseFloat(e.target.value);
            document.getElementById('frictionValue').textContent = e.target.value;
        });
    }
    
    // 시뮬레이션 초기화 및 시작
    initSimulationState();
    updateSimulation();
}