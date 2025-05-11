/**
 * simulation.js - 개선된 입자 물리 시뮬레이션
 * 사용자 상호작용과 물리법칙을 더 현실적으로 구현
 */
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('simulationCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 디버그 모드 설정
    const DEBUG = false;
    
    // Canvas 크기 설정 - 고해상도 지원 및 일관성 유지
    function resizeCanvas() {
        const devicePixelRatio = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        
        // CSS 크기와 실제 캔버스 크기 일치시키기
        canvas.width = rect.width * devicePixelRatio;
        canvas.height = rect.height * devicePixelRatio;
        
        // 스케일 적용으로 렌더링 해상도 조정
        ctx.scale(devicePixelRatio, devicePixelRatio);
        
        // CSS 크기 명시적 설정
        canvas.style.width = `${rect.width}px`;
        canvas.style.height = `${rect.height}px`;
        
        if (DEBUG) {
            console.log(`Canvas resized: ${canvas.width}x${canvas.height}, CSS: ${rect.width}x${rect.height}, DPR: ${devicePixelRatio}`);
        }
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 시뮬레이션 상태 및 설정
    const simulation = {
        particles: [],
        gravity: 9.8, // 중력 가속도 (m/s^2)
        friction: 0.01, // 마찰계수
        elasticity: 0.8, // 충돌 탄성계수
        airResistance: 0.001, // 공기저항 계수
        particleCount: 30, // 입자 수
        isRunning: true, // 시뮬레이션 실행 상태
        showVelocityVectors: false, // 속도 벡터 표시 여부
        showTrails: false, // 입자 궤적 표시 여부
        trails: [], // 입자 궤적 저장 배열
        colorMode: 'velocity', // 'velocity', 'size', 'random'
        lastTimestamp: 0, // 마지막 애니메이션 타임스탬프
        collisionDetection: true, // 입자 간 충돌 감지 여부
        maxSpeed: 1000, // 최대 허용 속도 (안정성을 위해)
        errorCount: 0, // 오류 카운터 (트러블슈팅용)
    };
    
    // 컨트롤 요소 초기화
    function initControls() {
        // 중력 컨트롤
        const gravityControl = document.getElementById('gravityControl');
        const gravityValue = document.getElementById('gravityValue');
        
        if (gravityControl && gravityValue) {
            gravityControl.value = simulation.gravity;
            gravityValue.textContent = simulation.gravity;
            
            gravityControl.addEventListener('input', function() {
                simulation.gravity = parseFloat(this.value);
                gravityValue.textContent = parseFloat(this.value).toFixed(1);
            });
        }
        
        // 마찰 컨트롤
        const frictionControl = document.getElementById('frictionControl');
        const frictionValue = document.getElementById('frictionValue');
        
        if (frictionControl && frictionValue) {
            frictionControl.value = simulation.friction;
            frictionValue.textContent = simulation.friction;
            
            frictionControl.addEventListener('input', function() {
                simulation.friction = parseFloat(this.value);
                frictionValue.textContent = parseFloat(this.value).toFixed(3);
            });
        }
        
        // 탄성 컨트롤
        const elasticityControl = document.getElementById('elasticityControl');
        const elasticityValue = document.getElementById('elasticityValue');
        
        if (elasticityControl && elasticityValue) {
            elasticityControl.value = simulation.elasticity;
            elasticityValue.textContent = simulation.elasticity;
            
            elasticityControl.addEventListener('input', function() {
                simulation.elasticity = parseFloat(this.value);
                elasticityValue.textContent = parseFloat(this.value).toFixed(2);
            });
        }
        
        // 공기저항 컨트롤
        const airResistanceControl = document.getElementById('airResistanceControl');
        const airResistanceValue = document.getElementById('airResistanceValue');
        
        if (airResistanceControl && airResistanceValue) {
            airResistanceControl.value = simulation.airResistance;
            airResistanceValue.textContent = simulation.airResistance;
            
            airResistanceControl.addEventListener('input', function() {
                simulation.airResistance = parseFloat(this.value);
                airResistanceValue.textContent = parseFloat(this.value).toFixed(4);
            });
        }
        
        // 입자 수 컨트롤
        const particleCountControl = document.getElementById('particleCountControl');
        const particleCountValue = document.getElementById('particleCountValue');
        
        if (particleCountControl && particleCountValue) {
            particleCountControl.value = simulation.particleCount;
            particleCountValue.textContent = simulation.particleCount;
            
            particleCountControl.addEventListener('input', function() {
                simulation.particleCount = parseInt(this.value);
                particleCountValue.textContent = this.value;
                resetParticles();
            });
        }
        
        // 충돌 감지 토글
        const collisionToggle = document.getElementById('collisionToggle');
        if (collisionToggle) {
            collisionToggle.checked = simulation.collisionDetection;
            collisionToggle.addEventListener('change', function() {
                simulation.collisionDetection = this.checked;
            });
        }
        
        // 속도 벡터 표시 토글
        const vectorToggle = document.getElementById('vectorToggle');
        if (vectorToggle) {
            vectorToggle.checked = simulation.showVelocityVectors;
            vectorToggle.addEventListener('change', function() {
                simulation.showVelocityVectors = this.checked;
            });
        }
        
        // 궤적 표시 토글
        const trailToggle = document.getElementById('trailToggle');
        if (trailToggle) {
            trailToggle.checked = simulation.showTrails;
            trailToggle.addEventListener('change', function() {
                simulation.showTrails = this.checked;
                if (!this.checked) {
                    simulation.trails = [];
                }
            });
        }
        
        // 색상 모드 선택
        const colorModeSelect = document.getElementById('colorModeSelect');
        if (colorModeSelect) {
            colorModeSelect.value = simulation.colorMode;
            colorModeSelect.addEventListener('change', function() {
                simulation.colorMode = this.value;
            });
        }
        
        // 시작 버튼
        const startButton = document.getElementById('startSimulation');
        if (startButton) {
            startButton.addEventListener('click', function() {
                simulation.isRunning = true;
                this.disabled = true;
                
                if (document.getElementById('stopSimulation')) {
                    document.getElementById('stopSimulation').disabled = false;
                }
            });
        }
        
        // 정지 버튼
        const stopButton = document.getElementById('stopSimulation');
        if (stopButton) {
            stopButton.addEventListener('click', function() {
                simulation.isRunning = false;
                this.disabled = true;
                
                if (document.getElementById('startSimulation')) {
                    document.getElementById('startSimulation').disabled = false;
                }
            });
        }
        
        // 초기화 버튼
        const resetButton = document.getElementById('resetSimulation');
        if (resetButton) {
            resetButton.addEventListener('click', resetParticles);
        }
        
        // 캔버스 클릭 이벤트 - 입자 추가
        canvas.addEventListener('click', function(e) {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // 새 입자 추가
            simulation.particles.push(createParticle(x, y));
            
            // 입자 수 업데이트
            simulation.particleCount = simulation.particles.length;
            if (particleCountValue) {
                particleCountValue.textContent = simulation.particleCount;
            }
            if (particleCountControl) {
                particleCountControl.value = simulation.particleCount;
            }
        });
    }
    
    // HSL 색상 생성 (속도 또는 크기 기반)
    function getParticleColor(particle) {
        switch(simulation.colorMode) {
            case 'velocity':
                // 속도에 따른 색상 변화
                const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
                const hue = 240 - Math.min(240, speed * 10); // 느림=파랑, 빠름=빨강
                return `hsl(${hue}, 80%, 60%)`;
            
            case 'size':
                // 크기에 따른 색상 변화
                const hueBySize = 360 * (particle.radius - 3) / 12; // 3~15 범위를 0~360 색상으로
                return `hsl(${hueBySize}, 80%, 60%)`;
                
            case 'random':
            default:
                // 생성 시 할당된 색상 사용
                return particle.color;
        }
    }
    
    // 새 입자 생성
    function createParticle(x, y) {
        return {
            x: x || Math.random() * canvas.clientWidth,
            y: y || Math.random() * canvas.clientHeight,
            vx: (Math.random() - 0.5) * 5, // 초기 x방향 속도
            vy: (Math.random() - 0.5) * 5, // 초기 y방향 속도
            radius: 3 + Math.random() * 12, // 3~15 사이의 반지름
            color: `hsl(${Math.random() * 360}, 80%, 60%)`, // 랜덤 HSL 색상
            mass: 0, // 나중에 반지름 기반으로 계산
        };
    }
    
    // 입자 초기화
    function resetParticles() {
        simulation.particles = [];
        simulation.trails = [];
        simulation.errorCount = 0;
        
        for (let i = 0; i < simulation.particleCount; i++) {
            const particle = createParticle();
            // 질량은 반지름의 제곱에 비례 (원의 넓이에 비례)
            particle.mass = particle.radius * particle.radius;
            simulation.particles.push(particle);
        }
    }
    
    // 속도 제한 함수 추가
    function limitSpeed(particle) {
        const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
        if (speed > simulation.maxSpeed) {
            const ratio = simulation.maxSpeed / speed;
            particle.vx *= ratio;
            particle.vy *= ratio;
        }
    }
    
    // 경계 벗어남 확인 및 수정
    function keepParticleInBounds(particle) {
        const clientWidth = canvas.clientWidth;
        const clientHeight = canvas.clientHeight;
        
        // NaN 체크 - 값이 정의되지 않은 경우 리셋
        if (isNaN(particle.x) || isNaN(particle.y) || 
            isNaN(particle.vx) || isNaN(particle.vy) ||
            !isFinite(particle.x) || !isFinite(particle.y) ||
            !isFinite(particle.vx) || !isFinite(particle.vy)) {
            
            particle.x = clientWidth / 2;
            particle.y = clientHeight / 2;
            particle.vx = 0;
            particle.vy = 0;
            simulation.errorCount++;
            
            if (DEBUG) {
                console.warn("NaN or Infinity detected, particle reset");
            }
            return;
        }
        
        // 경계를 벗어난 경우 강제로 경계 내로 조정
        if (particle.x < particle.radius) {
            particle.x = particle.radius;
        } else if (particle.x > clientWidth - particle.radius) {
            particle.x = clientWidth - particle.radius;
        }
        
        if (particle.y < particle.radius) {
            particle.y = particle.radius;
        } else if (particle.y > clientHeight - particle.radius) {
            particle.y = clientHeight - particle.radius;
        }
    }
    
    // 입자 물리 업데이트
    function updateParticle(particle, deltaTime) {
        // 시간 간격 제한 - 물리 안정성 향상
        const dt = Math.min(deltaTime, 33) / 1000; // 최대 33ms (약 30fps)
        
        // 중력 적용
        particle.vy += simulation.gravity * dt;
        
        // 공기저항 적용 (속도 제곱에 비례)
        const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
        if (speed > 0) {
            const dragForce = simulation.airResistance * speed * speed;
            const dragX = (dragForce * particle.vx) / speed;
            const dragY = (dragForce * particle.vy) / speed;
            particle.vx -= dragX * dt;
            particle.vy -= dragY * dt;
        }
        
        // 속도 제한 (안정성 향상)
        limitSpeed(particle);
        
        // 위치 업데이트 (이전 위치 복사해 두기)
        const prevX = particle.x;
        const prevY = particle.y;
        
        particle.x += particle.vx * dt * 60; // 60fps 기준 속도 보정
        particle.y += particle.vy * dt * 60;
        
        // 벽 충돌 처리
        handleWallCollision(particle);
        
        // 경계 검사 및 수정 (강화된 안정성)
        keepParticleInBounds(particle);
        
        // 입자 간 충돌 처리
        if (simulation.collisionDetection) {
            for (let i = 0; i < simulation.particles.length; i++) {
                const otherParticle = simulation.particles[i];
                if (particle === otherParticle) continue;
                
                handleParticleCollision(particle, otherParticle);
            }
        }
    }
    
    // 벽 충돌 처리
    function handleWallCollision(particle) {
        const clientWidth = canvas.clientWidth;
        const clientHeight = canvas.clientHeight;
        
        // 좌우 벽 충돌
        if (particle.x - particle.radius < 0) {
            particle.x = particle.radius; // 벽 안쪽으로 보정
            particle.vx = Math.abs(particle.vx) * simulation.elasticity;
        } else if (particle.x + particle.radius > clientWidth) {
            particle.x = clientWidth - particle.radius; // 벽 안쪽으로 보정
            particle.vx = -Math.abs(particle.vx) * simulation.elasticity;
        }
        
        // 상하 벽 충돌
        if (particle.y - particle.radius < 0) {
            particle.y = particle.radius; // 천장 안쪽으로 보정
            particle.vy = Math.abs(particle.vy) * simulation.elasticity;
        } else if (particle.y + particle.radius > clientHeight) {
            particle.y = clientHeight - particle.radius; // 바닥 안쪽으로 보정
            particle.vy = -Math.abs(particle.vy) * simulation.elasticity;
            
            // 바닥에 있을 때 추가 마찰 적용
            particle.vx *= (1 - simulation.friction);
        }
    }
    
    // 입자 간 충돌 처리
    function handleParticleCollision(p1, p2) {
        // 두 입자 사이의 거리 계산
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const minDistance = p1.radius + p2.radius;
        
        // 충돌 감지 (반지름 합보다 거리가 작을 때)
        if (distance < minDistance) {
            // 충돌 각도 계산
            const angle = Math.atan2(dy, dx);
            
            // 두 입자 분리 (겹치지 않도록)
            const overlap = minDistance - distance;
            
            // 질량 기반 위치 조정 (더 가벼운 입자가 더 많이 밀려남)
            const totalMass = p1.mass + p2.mass;
            const p1Ratio = p1.mass / totalMass;
            const p2Ratio = p2.mass / totalMass;
            
            // 겹침 해결을 위한 최소 이동 거리 (안정성 보장)
            const minAdjustment = 0.01; // 최소 이동 거리
            
            // 첫 번째 입자 위치 조정
            const p1AdjustX = Math.cos(angle) * overlap * p2Ratio;
            const p1AdjustY = Math.sin(angle) * overlap * p2Ratio;
            p1.x -= Math.max(p1AdjustX, minAdjustment * Math.sign(p1AdjustX));
            p1.y -= Math.max(p1AdjustY, minAdjustment * Math.sign(p1AdjustY));
            
            // 두 번째 입자 위치 조정
            const p2AdjustX = Math.cos(angle) * overlap * p1Ratio;
            const p2AdjustY = Math.sin(angle) * overlap * p1Ratio;
            p2.x += Math.max(p2AdjustX, minAdjustment * Math.sign(p2AdjustX));
            p2.y += Math.max(p2AdjustY, minAdjustment * Math.sign(p2AdjustY));
            
            // 경계 재확인
            keepParticleInBounds(p1);
            keepParticleInBounds(p2);
            
            // 접선 및 법선 속도 성분 계산
            // 법선 방향 속도 (충돌 방향)
            const p1vn = p1.vx * Math.cos(angle) + p1.vy * Math.sin(angle);
            const p2vn = p2.vx * Math.cos(angle) + p2.vy * Math.sin(angle);
            
            // 접선 방향 속도 (충돌면 접선)
            const p1vt = -p1.vx * Math.sin(angle) + p1.vy * Math.cos(angle);
            const p2vt = -p2.vx * Math.sin(angle) + p2.vy * Math.cos(angle);
            
            // 충돌 후 법선 방향 속도 (탄성 계수 적용)
            const p1vnAfter = ((p1vn * (p1.mass - p2.mass)) + (2 * p2.mass * p2vn)) / totalMass;
            const p2vnAfter = ((p2vn * (p2.mass - p1.mass)) + (2 * p1.mass * p1vn)) / totalMass;
            
            // 탄성계수 적용
            const p1vnFinal = p1vnAfter * simulation.elasticity;
            const p2vnFinal = p2vnAfter * simulation.elasticity;
            
            // 속도 벡터 재구성
            p1.vx = p1vnFinal * Math.cos(angle) - p1vt * Math.sin(angle);
            p1.vy = p1vnFinal * Math.sin(angle) + p1vt * Math.cos(angle);
            p2.vx = p2vnFinal * Math.cos(angle) - p2vt * Math.sin(angle);
            p2.vy = p2vnFinal * Math.sin(angle) + p2vt * Math.cos(angle);
            
            // 속도 제한 재확인
            limitSpeed(p1);
            limitSpeed(p2);
        }
    }
    
    // 화면 업데이트
    function render() {
        // 화면 지우기
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 디버그: 캔버스 경계 시각화
        if (DEBUG) {
            ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
            ctx.strokeRect(0, 0, canvas.clientWidth, canvas.clientHeight);
        }
        
        // 궤적 그리기
        if (simulation.showTrails && simulation.trails.length > 0) {
            ctx.globalAlpha = 0.3;
            for (let i = 0; i < simulation.trails.length; i++) {
                const trail = simulation.trails[i];
                const particle = simulation.particles[i % simulation.particles.length];
                
                if (trail.length > 1) {
                    ctx.beginPath();
                    ctx.moveTo(trail[0].x, trail[0].y);
                    
                    for (let j = 1; j < trail.length; j++) {
                        ctx.lineTo(trail[j].x, trail[j].y);
                    }
                    
                    ctx.strokeStyle = getParticleColor(particle);
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            }
            ctx.globalAlpha = 1.0;
        }
        
        // 입자 그리기
        for (let i = 0; i < simulation.particles.length; i++) {
            const particle = simulation.particles[i];
            
            // 입자 원 그리기
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fillStyle = getParticleColor(particle);
            ctx.fill();
            
            // 테두리 추가
            ctx.strokeStyle = 'rgba(0, 0, 0, 0.2)';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            // 속도 벡터 표시
            if (simulation.showVelocityVectors) {
                const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
                const vectorLength = Math.min(speed * 3, 50); // 최대 길이 제한
                
                if (speed > 0.1) { // 적어도 어느정도 움직이는 입자만
                    ctx.beginPath();
                    ctx.moveTo(particle.x, particle.y);
                    ctx.lineTo(
                        particle.x + (particle.vx / speed) * vectorLength,
                        particle.y + (particle.vy / speed) * vectorLength
                    );
                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            }
        }
        
        // 성능 정보 표시
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.font = '14px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`입자 수: ${simulation.particles.length}`, 10, 20);
        ctx.fillText(`FPS: ${Math.round(1000 / Math.max(1, simulation.deltaTime))}`, 10, 40);
        
        // 디버그 정보 표시
        if (DEBUG) {
            ctx.fillText(`Canvas: ${canvas.width}x${canvas.height}`, 10, 60);
            ctx.fillText(`Display: ${canvas.clientWidth}x${canvas.clientHeight}`, 10, 80);
            ctx.fillText(`Errors: ${simulation.errorCount}`, 10, 100);
        }
    }
    
    // 애니메이션 루프
    function animate(timestamp) {
        // 시간 간격 계산
        if (!simulation.lastTimestamp) {
            simulation.lastTimestamp = timestamp;
        }
        const deltaTime = timestamp - simulation.lastTimestamp;
        simulation.lastTimestamp = timestamp;
        simulation.deltaTime = deltaTime;
        
        // 시뮬레이션 실행 중이면 물리 업데이트
        if (simulation.isRunning) {
            // 궤적 기록
            if (simulation.showTrails) {
                for (let i = 0; i < simulation.particles.length; i++) {
                    if (!simulation.trails[i]) {
                        simulation.trails[i] = [];
                    }
                    
                    // 궤적 최대 길이 제한
                    if (simulation.trails[i].length > 30) {
                        simulation.trails[i].shift();
                    }
                    
                    // 현재 위치 추가
                    simulation.trails[i].push({
                        x: simulation.particles[i].x,
                        y: simulation.particles[i].y
                    });
                }
            }
            
            // 입자 업데이트
            for (const particle of simulation.particles) {
                updateParticle(particle, deltaTime);
            }
        }
        
        // 화면 렌더링
        render();
        
        // 다음 프레임 요청
        requestAnimationFrame(animate);
    }
    
    // 시뮬레이션 초기화 및 시작
    function init() {
        try {
            resetParticles();
            initControls();
            requestAnimationFrame(animate);
        } catch (e) {
            console.error("시뮬레이션 초기화 오류:", e);
        }
    }
    
    init();
});