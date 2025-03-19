/**
 * simulation.js - 간단한 물리 시뮬레이션
 * 심플한 입자 애니메이션 구현
 */
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('simulationCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Canvas 크기 설정
    function resizeCanvas() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 입자 생성
    const particles = [];
    const particleCount = 20;
    
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: 3 + Math.random() * 5,
        color: `hsl(${Math.random() * 360}, 70%, 60%)`,
        velocityX: Math.random() * 2 - 1,
        velocityY: Math.random() * 2 - 1
      });
    }
    
    // 애니메이션 함수
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach(particle => {
        // 위치 업데이트
        particle.x += particle.velocityX;
        particle.y += particle.velocityY;
        
        // 벽 충돌 처리
        if (particle.x - particle.radius < 0 || 
            particle.x + particle.radius > canvas.width) {
          particle.velocityX *= -1;
        }
        
        if (particle.y - particle.radius < 0 || 
            particle.y + particle.radius > canvas.height) {
          particle.velocityY *= -1;
        }
        
        // 입자 그리기
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.fill();
      });
      
      requestAnimationFrame(animate);
    }
    
    // 애니메이션 시작
    animate();
  });