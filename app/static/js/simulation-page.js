/**
 * simulation-page.js - 시뮬레이션 페이지 전용 스크립트
 */
document.addEventListener('DOMContentLoaded', function() {
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
    
    // 시뮬레이션 설정
    const simulation = {
      particles: [],
      gravity: 9.8,
      friction: 0.01,
      running: false
    };
    
    // 입자 초기화
    function initParticles() {
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
    
    // 시뮬레이션 업데이트 및 렌더링
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
        
        // 마찰력 적용
        particle.vx *= (1 - simulation.friction);
        particle.vy *= (1 - simulation.friction);
        
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
    
    // 컨트롤 초기화
    const startButton = document.getElementById('startSimulation');
    const stopButton = document.getElementById('stopSimulation');
    const resetButton = document.getElementById('resetSimulation');
    const gravityControl = document.getElementById('gravityControl');
    const frictionControl = document.getElementById('frictionControl');
    
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
        initParticles();
        if (!simulation.running) {
          updateSimulation();
        }
      });
    }
    
    if (gravityControl) {
      gravityControl.addEventListener('input', function(e) {
        simulation.gravity = parseFloat(e.target.value);
        document.getElementById('gravityValue').textContent = e.target.value;
      });
    }
    
    if (frictionControl) {
      frictionControl.addEventListener('input', function(e) {
        simulation.friction = parseFloat(e.target.value);
        document.getElementById('frictionValue').textContent = e.target.value;
      });
    }
    
    // 시뮬레이션 초기화 및 시작
    initParticles();
    updateSimulation();
    simulation.running = true;
  });