/**
 * simulation.js - 간소화된 5개 입자 완전탄성충돌 시스템
 * - 중력과 마찰 없음
 * - 5개의 입자만 사용
 * - 속도에 따른 색상 변환 적용
 * - 입자 간 완전탄성충돌 구현
 */
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('simulationCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 캔버스 크기 설정
    function resizeCanvas() {
        const devicePixelRatio = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        canvas.width = rect.width * devicePixelRatio;
        canvas.height = rect.height * devicePixelRatio;
        
        ctx.scale(devicePixelRatio, devicePixelRatio);
        
        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 시뮬레이션 설정
    const simulation = {
        particles: [],
        isRunning: true,
        particleCount: 5, // 5개로 제한
        lastTimestamp: 0,  // simulation 객체에 저장하여 오류 방지
        colorMode: 'velocity' // 속도 기반 색상
    };
    
    // 새 입자 생성
    function createParticle(x, y) {
        const clientWidth = canvas.clientWidth;
        const clientHeight = canvas.clientHeight;
        
        // 사용자가 클릭한 위치가 있으면 그 위치에, 없으면 랜덤 위치에 생성
        const posX = x || Math.random() * clientWidth;
        const posY = y || Math.random() * clientHeight;
        
        const radius = 10 + Math.random() * 20; // 10~30 사이의 반지름
        
        return {
            x: posX,
            y: posY,
            vx: (Math.random() - 0.5) * 4, // 초기 x 방향 속도
            vy: (Math.random() - 0.5) * 4, // 초기 y 방향 속도
            radius: radius,
            color: `hsl(${Math.random() * 360}, 80%, 60%)`, // 초기 랜덤 색상
            // 질량은 반지름의 제곱에 비례 (원의 면적)
            mass: radius * radius
        };
    }
    
    // 입자 초기화
    function resetParticles() {
        simulation.particles = [];
        for (let i = 0; i < simulation.particleCount; i++) {
            simulation.particles.push(createParticle());
        }
    }
    
    // 입자 물리 업데이트 (중력, 마찰 없음)
    function updateParticle(particle, deltaTime) {
        const dt = Math.min(deltaTime, 33) / 1000; // 최대 33ms (약 30fps)
        
        // 위치 업데이트 (중력, 마찰 없음)
        particle.x += particle.vx * dt * 60; // 60fps 기준 속도 보정
        particle.y += particle.vy * dt * 60;
        
        // 벽 충돌 처리 (감속 없음, 방향만 바꿈)
        const clientWidth = canvas.clientWidth;
        const clientHeight = canvas.clientHeight;
        
        if (particle.x - particle.radius < 0) {
            particle.x = particle.radius;
            particle.vx = Math.abs(particle.vx);
        } else if (particle.x + particle.radius > clientWidth) {
            particle.x = clientWidth - particle.radius;
            particle.vx = -Math.abs(particle.vx);
        }
        
        if (particle.y - particle.radius < 0) {
            particle.y = particle.radius;
            particle.vy = Math.abs(particle.vy);
        } else if (particle.y + particle.radius > clientHeight) {
            particle.y = clientHeight - particle.radius;
            particle.vy = -Math.abs(particle.vy);
        }
    }
    
    // 입자 간 충돌 감지 및 처리
    function handleParticleCollisions() {
        const particles = simulation.particles;
        
        // 모든 입자 쌍에 대해 충돌 확인
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                
                // 두 입자 사이의 거리 계산
                const dx = p2.x - p1.x;
                const dy = p2.y - p1.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // 충돌 감지 (반지름 합보다 거리가 작으면 충돌)
                if (distance < p1.radius + p2.radius) {
                    // 충돌 각도 계산
                    const angle = Math.atan2(dy, dx);
                    
                    // 겹침 수정 (입자가 서로 겹치지 않도록)
                    const overlap = (p1.radius + p2.radius) - distance;
                    const moveX = Math.cos(angle) * overlap * 0.5;
                    const moveY = Math.sin(angle) * overlap * 0.5;
                    
                    // 입자 위치 조정
                    p1.x -= moveX;
                    p1.y -= moveY;
                    p2.x += moveX;
                    p2.y += moveY;
                    
                    // 완전탄성충돌 계산
                    // 충돌 방향으로의 속도 성분 계산
                    const v1 = (p1.vx * Math.cos(angle) + p1.vy * Math.sin(angle));
                    const v2 = (p2.vx * Math.cos(angle) + p2.vy * Math.sin(angle));
                    
                    // 충돌 직각 방향의 속도 성분 (변경되지 않음)
                    const v1Perpendicular = -p1.vx * Math.sin(angle) + p1.vy * Math.cos(angle);
                    const v2Perpendicular = -p2.vx * Math.sin(angle) + p2.vy * Math.cos(angle);
                    
                    // 질량을 고려한 운동량 보존 충돌 계산
                    const totalMass = p1.mass + p2.mass;
                    const v1Final = ((p1.mass - p2.mass) * v1 + 2 * p2.mass * v2) / totalMass;
                    const v2Final = ((p2.mass - p1.mass) * v2 + 2 * p1.mass * v1) / totalMass;
                    
                    // 새로운 속도 벡터 계산
                    p1.vx = Math.cos(angle) * v1Final - Math.sin(angle) * v1Perpendicular;
                    p1.vy = Math.sin(angle) * v1Final + Math.cos(angle) * v1Perpendicular;
                    p2.vx = Math.cos(angle) * v2Final - Math.sin(angle) * v2Perpendicular;
                    p2.vy = Math.sin(angle) * v2Final + Math.cos(angle) * v2Perpendicular;
                }
            }
        }
    }
    
    // 속도에 따른 색상 계산
    function getParticleColor(particle) {
        // 속도에 따른 색상 변화: 느림=파랑, 빠름=빨강
        const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
        const hue = 240 - Math.min(240, speed * 30);
        return `hsl(${hue}, 80%, 60%)`;
    }
    
    // 화면 업데이트
    function render() {
        // 화면 지우기
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 입자 그리기
        for (const particle of simulation.particles) {
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fillStyle = getParticleColor(particle);
            ctx.fill();
            
            // 테두리 추가
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }
        
        // 정보 표시
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.font = '14px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`입자 수: ${simulation.particles.length}`, 10, 20);
        ctx.fillText(`클릭하여 입자에 힘 가하기`, 10, 40);
    }
    
    // 애니메이션 루프
    function animate(timestamp) {
        // 시간 간격 계산 - lastTimestamp를 simulation 객체에 저장하여 오류 방지
        if (!simulation.lastTimestamp) {
            simulation.lastTimestamp = timestamp;
        }
        const deltaTime = timestamp - simulation.lastTimestamp;
        simulation.lastTimestamp = timestamp;
        
        // 시뮬레이션 실행 중이면 물리 업데이트
        if (simulation.isRunning) {
            // 각 입자 개별 업데이트
            for (const particle of simulation.particles) {
                updateParticle(particle, deltaTime);
            }
            
            // 입자 간 충돌 처리
            handleParticleCollisions();
        }
        
        // 화면 렌더링
        render();
        
        // 다음 프레임 요청
        requestAnimationFrame(animate);
    }
    
    // 마우스 클릭으로 입자 움직임 변경
    canvas.addEventListener('click', function(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 클릭한 방향으로 입자들에게 힘 적용
        for (const particle of simulation.particles) {
            const dx = x - particle.x;
            const dy = y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance > 0) {
                const force = 5; // 힘의 크기
                particle.vx += (dx / distance) * force;
                particle.vy += (dy / distance) * force;
            }
        }
    });
    
    // 초기화 및 시작
    function init() {
        resetParticles();
        requestAnimationFrame(animate);
    }
    
    init();
});