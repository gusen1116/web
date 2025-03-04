// static/js/simulation.js
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('simulationCanvas');
    const ctx = canvas.getContext('2d');
    const socket = io();

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
    function initSimulation() {
        // 초기 입자 생성
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
    document.getElementById('startSimulation').addEventListener('click', function() {
        simulation.running = true;
        updateSimulation();
    });

    document.getElementById('stopSimulation').addEventListener('click', function() {
        simulation.running = false;
    });

    document.getElementById('resetSimulation').addEventListener('click', function() {
        simulation.particles = [];
        initSimulation();
        if (!simulation.running) {
            updateSimulation();
        }
    });

    // 매개변수 조정
    document.getElementById('gravityControl').addEventListener('input', function(e) {
        simulation.gravity = parseFloat(e.target.value);
    });

    document.getElementById('frictionControl').addEventListener('input', function(e) {
        simulation.friction = parseFloat(e.target.value);
    });

    // 웹소켓 이벤트
    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('update_data', function(data) {
        // 라즈베리파이에서 받은 데이터로 시뮬레이션 업데이트
        console.log('Received data:', data);
        // 데이터에 따라 시뮬레이션 파라미터 조정
    });

    // 시뮬레이션 초기화 및 시작
    initSimulation();
    updateSimulation();
});