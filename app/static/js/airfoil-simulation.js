/**
 * airfoil-simulation.js - 비행기 날개 주변 유체 흐름 시뮬레이션
 */

document.addEventListener('DOMContentLoaded', function() {
    // 캔버스 및 컨텍스트 설정
    const canvas = document.getElementById('airfoilCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 캔버스 크기 설정
    function resizeCanvas() {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // 시뮬레이션 설정 및 상태
    const simulation = {
        // 유체 특성
        fluidVelocity: 50,       // m/s
        fluidVelocityKt: 97.2,   // knots
        fluidPressure: 101.325,  // kPa (1 atm)
        altitude: 0,             // meters above sea level
        fluidTemperature: 15,    // Celsius
        fluidDensity: 1.225,     // kg/m³ (at sea level, 15°C)
        
        // 날개 형상 설정
        chord: 250,              // 날개 시위길이 (픽셀)
        thickness: 12,           // 날개 두께 (시위길이의 %)
        
        // 고양력 장치 및 조종면 설정
        flapDeflection: 0,       // 플랩 각도 (도)
        slatExtension: 0,        // 슬랫 확장 (%)
        spoilerDeflection: 0,    // 스포일러 각도 (도)
        
        // 격자 및 입자 설정
        particles: [],
        gridSize: 8,             // 격자 크기 (픽셀)
        particleCount: 150,      // 입자 수
        
        // 시뮬레이션 상태
        running: true,
        showPressure: true,      // 압력 분포 표시
        showParticles: true,     // 유체 입자 표시
        showVectors: true,       // 속도 벡터 표시
        
        // 색상 스케일 설정 (압력 시각화)
        minPressure: 97,         // kPa
        maxPressure: 104         // kPa
    };
    
    // 날개 형상 및 격자 데이터
    let airfoilPoints = [];
    let pressureField = [];
    let velocityField = [];
    
    // 유틸리티 함수들
    function transformX(x) {
        return (x / 100 * simulation.chord) + canvas.width * 0.3;
    }
    
    function transformY(y) {
        return canvas.height / 2 - (y / 100 * simulation.chord);
    }
    
    // 유체 압력에 따른 색상 계산
    function getPressureColor(pressure) {
        const normalizedPressure = (pressure - simulation.minPressure) / 
                                (simulation.maxPressure - simulation.minPressure);
        
        const r = Math.round(Math.max(0, Math.min(255, normalizedPressure * 255)));
        const b = Math.round(Math.max(0, Math.min(255, 255 - normalizedPressure * 255)));
        const g = Math.round(Math.max(0, Math.min(100, 100 - Math.abs(normalizedPressure - 0.5) * 200)));
        
        return `rgb(${r}, ${g}, ${b})`;
    }

    // 날개 형상 생성
    function generateAirfoilShape() {
        airfoilPoints = [];
        
        // 기본 NACA 4-시리즈 에어포일 형상 근사
        for (let x = 0; x <= 100; x++) {
            // 두께 분포
            const t = simulation.thickness / 100;
            const xc = x / 100;
            
            // 캠버 및 두께 계산
            let yt = 5 * t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
            
            // 대칭 날개 형상
            airfoilPoints.push({ x: x, yu: yt * 100, yl: -yt * 100 });
        }
        
        // 플랩 적용
        if (simulation.flapDeflection > 0) {
            const flapHingeX = 70;  // 플랩 힌지 위치 (시위길이의 %)
            
            for (let i = 0; i < airfoilPoints.length; i++) {
                if (airfoilPoints[i].x >= flapHingeX) {
                    // 플랩 각도에 따른 회전 계산
                    const angle = simulation.flapDeflection * Math.PI / 180;
                    const relX = airfoilPoints[i].x - flapHingeX;
                    
                    // 상면 변환
                    const oldYu = airfoilPoints[i].yu;
                    airfoilPoints[i].yu = (relX * Math.sin(angle) + oldYu * Math.cos(angle)) + 
                                         (flapHingeX * Math.tan(angle));
                    
                    // 하면 변환
                    const oldYl = airfoilPoints[i].yl;
                    airfoilPoints[i].yl = (relX * Math.sin(angle) + oldYl * Math.cos(angle)) + 
                                         (flapHingeX * Math.tan(angle));
                }
            }
        }
        
        // 슬랫 적용
        if (simulation.slatExtension > 0) {
            // 새로운 슬랫 형상 생성
            const slatPoints = [];
            const slatLength = 20;  // 슬랫 길이 (시위길이의 %)
            const extensionPct = simulation.slatExtension / 100;
            
            for (let x = 0; x <= slatLength; x++) {
                // 슬랫 두께 분포
                const t = simulation.thickness * 0.8 / 100;  // 슬랫은 약간 얇게
                const xc = x / slatLength;
                
                // 슬랫 캠버 및 두께
                let yt = 5 * t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
                
                // 슬랫 위치 조정
                const offsetX = -slatLength * extensionPct * 0.7;
                const offsetY = -slatLength * extensionPct * 0.3;
                
                slatPoints.push({ 
                    x: offsetX + x * (1 - 0.3 * extensionPct), 
                    yu: offsetY + yt * 100, 
                    yl: offsetY - yt * 100 
                });
            }
            
            // 슬랫을 기존 형상에 추가
            airfoilPoints = [...slatPoints, ...airfoilPoints.slice(slatLength)];
        }
        
        // 스포일러 적용
        if (simulation.spoilerDeflection > 0) {
            const spoilerStartX = 50;  // 스포일러 시작 위치 (시위길이의 %)
            const spoilerEndX = 70;    // 스포일러 끝 위치 (시위길이의 %)
            
            for (let i = 0; i < airfoilPoints.length; i++) {
                if (airfoilPoints[i].x >= spoilerStartX && airfoilPoints[i].x <= spoilerEndX) {
                    // 스포일러 각도에 따른 상면 변환
                    const spoilerPct = (airfoilPoints[i].x - spoilerStartX) / (spoilerEndX - spoilerStartX);
                    const deflection = simulation.spoilerDeflection * Math.sin(Math.PI * spoilerPct) * 0.15;
                    airfoilPoints[i].yu += deflection * simulation.chord / 100;
                }
            }
        }
    }
    
    // 유체 격자 초기화
    function initFluidGrid() {
        const gridCols = Math.ceil(canvas.width / simulation.gridSize);
        const gridRows = Math.ceil(canvas.height / simulation.gridSize);
        
        pressureField = new Array(gridRows);
        velocityField = new Array(gridRows);
        
        for (let i = 0; i < gridRows; i++) {
            pressureField[i] = new Array(gridCols).fill(simulation.fluidPressure);
            velocityField[i] = new Array(gridCols);
            
            for (let j = 0; j < gridCols; j++) {
                velocityField[i][j] = {
                    u: simulation.fluidVelocity,  // x방향 속도
                    v: 0                          // y방향 속도
                };
            }
        }
    }
    
    // 입자 초기화
    function initParticles() {
        simulation.particles = [];
        
        for (let i = 0; i < simulation.particleCount; i++) {
            simulation.particles.push({
                x: Math.random() * (canvas.width / 3),
                y: Math.random() * canvas.height,
                vx: 0,
                vy: 0,
                age: Math.random() * 100
            });
        }
    }

    // 공기 밀도 업데이트 함수
    function updateAirDensity() {
        // 온도와 압력에 따른 밀도 계산 (이상 기체 법칙 근사)
        const R = 287.05; // 건조 공기의 기체 상수 (J/kg·K)
        const T = simulation.fluidTemperature + 273.15; // 켈빈 온도
        const P = simulation.fluidPressure * 1000; // Pa로 변환
        
        simulation.fluidDensity = P / (R * T);
    }

    // 날개 형상 렌더링
    function renderAirfoil() {
        ctx.beginPath();
        
        // 상면 그리기
        ctx.moveTo(transformX(airfoilPoints[0].x), transformY(airfoilPoints[0].yu));
        for (let i = 1; i < airfoilPoints.length; i++) {
            ctx.lineTo(transformX(airfoilPoints[i].x), transformY(airfoilPoints[i].yu));
        }
        
        // 하면 그리기 (뒤에서부터)
        for (let i = airfoilPoints.length - 1; i >= 0; i--) {
            ctx.lineTo(transformX(airfoilPoints[i].x), transformY(airfoilPoints[i].yl));
        }
        
        ctx.closePath();
        ctx.fillStyle = '#f0f0f0';
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();
    }
    
    // 압력장 렌더링
    function renderPressureField() {
        if (!simulation.showPressure) return;
        
        const imgData = ctx.createImageData(canvas.width, canvas.height);
        const data = imgData.data;
        
        for (let i = 0; i < pressureField.length; i++) {
            for (let j = 0; j < pressureField[i].length; j++) {
                const pressure = pressureField[i][j];
                const color = getPressureColor(pressure);
                
                // RGB 색상 파싱
                const r = parseInt(color.substring(4, color.indexOf(',')));
                const g = parseInt(color.substring(color.indexOf(',') + 1, color.lastIndexOf(',')));
                const b = parseInt(color.substring(color.lastIndexOf(',') + 1, color.indexOf(')')));
                
                // 격자 영역을 픽셀로 채우기
                for (let y = i * simulation.gridSize; y < (i + 1) * simulation.gridSize; y++) {
                    for (let x = j * simulation.gridSize; x < (j + 1) * simulation.gridSize; x++) {
                        if (x < canvas.width && y < canvas.height) {
                            const pos = (y * canvas.width + x) * 4;
                            data[pos] = r;
                            data[pos + 1] = g;
                            data[pos + 2] = b;
                            data[pos + 3] = 120; // 알파 (투명도)
                        }
                    }
                }
            }
        }
        
        ctx.putImageData(imgData, 0, 0);
    }
    
    // 유체 입자 렌더링
    function renderParticles() {
        if (!simulation.showParticles) return;
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        
        for (const p of simulation.particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    // 속도 벡터장 렌더링
    function renderVelocityField() {
        if (!simulation.showVectors) return;
        
        const vectorScale = 2.0;
        const step = Math.floor(simulation.gridSize * 3);
        
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 1;
        
        for (let i = 0; i < velocityField.length; i += step) {
            for (let j = 0; j < velocityField[i].length; j += step) {
                if (velocityField[i][j]) {
                    const x = j * simulation.gridSize;
                    const y = i * simulation.gridSize;
                    const length = Math.sqrt(velocityField[i][j].u**2 + velocityField[i][j].v**2);
                    
                    if (length > 0) {
                        const dx = velocityField[i][j].u / length * step * vectorScale;
                        const dy = velocityField[i][j].v / length * step * vectorScale;
                        
                        ctx.beginPath();
                        ctx.moveTo(x, y);
                        ctx.lineTo(x + dx, y + dy);
                        
                        // 화살표 머리 그리기
                        const arrowLength = 5;
                        const angle = Math.atan2(dy, dx);
                        ctx.lineTo(
                            x + dx - arrowLength * Math.cos(angle - Math.PI / 6),
                            y + dy - arrowLength * Math.sin(angle - Math.PI / 6)
                        );
                        ctx.moveTo(x + dx, y + dy);
                        ctx.lineTo(
                            x + dx - arrowLength * Math.cos(angle + Math.PI / 6),
                            y + dy - arrowLength * Math.sin(angle + Math.PI / 6)
                        );
                        ctx.stroke();
                    }
                }
            }
        }
    }
    
    // 데이터 오버레이 렌더링
    function renderDataOverlay() {
        const textX = 20;
        let textY = 30;
        const lineHeight = 20;
        
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(10, 10, 290, 230);
        
        ctx.font = '14px Arial';
        ctx.fillStyle = 'white';
        
        // 시뮬레이션 파라미터 표시
        ctx.fillText(`속도: ${simulation.fluidVelocity.toFixed(1)} m/s (${simulation.fluidVelocityKt.toFixed(1)} kt)`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`고도: ${simulation.altitude.toFixed(0)} m`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`기압: ${simulation.fluidPressure.toFixed(1)} kPa`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`온도: ${simulation.fluidTemperature.toFixed(1)} °C`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`공기 밀도: ${simulation.fluidDensity.toFixed(3)} kg/m³`, textX, textY);
        textY += lineHeight * 1.5;
        
        ctx.fillText(`플랩: ${simulation.flapDeflection.toFixed(1)}°`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`슬랫: ${simulation.slatExtension.toFixed(1)}%`, textX, textY);
        textY += lineHeight;
        ctx.fillText(`스포일러: ${simulation.spoilerDeflection.toFixed(1)}°`, textX, textY);
        textY += lineHeight * 1.5;
        
        // 계산된 공역학적 특성
        const aoaText = 5; // Angle of Attack (고정값)
        ctx.fillText(`받음각(AoA): ${aoaText.toFixed(1)}°`, textX, textY);
        textY += lineHeight;
        
        // 압력범례
        textY += lineHeight;
        const gradientWidth = 200;
        const gradientHeight = 15;
        const gradientX = textX;
        const gradientY = textY;
        
        // 압력 그라디언트 그리기
        const gradient = ctx.createLinearGradient(gradientX, 0, gradientX + gradientWidth, 0);
        gradient.addColorStop(0, 'blue');
        gradient.addColorStop(0.5, 'purple');
        gradient.addColorStop(1, 'red');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(gradientX, gradientY, gradientWidth, gradientHeight);
        
        // 압력 범례 테두리
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.strokeRect(gradientX, gradientY, gradientWidth, gradientHeight);
        
        // 압력 범례 텍스트
        ctx.fillStyle = 'white';
        ctx.fillText('저압', gradientX, gradientY + gradientHeight + 15);
        ctx.fillText('고압', gradientX + gradientWidth - 20, gradientY + gradientHeight + 15);
    }
    
    // 유체 속도장 계산
    function calculateFlowField() {
        // 자유류 속도 (원거리 경계조건)
        const U_inf = simulation.fluidVelocity;
        
        // 날개 형상 기준점 (1/4 시위점)
        const referenceX = canvas.width * 0.3 + simulation.chord * 0.25;
        const referenceY = canvas.height / 2;
        
        // 압력 분포 초기화
        for (let i = 0; i < pressureField.length; i++) {
            for (let j = 0; j < pressureField[i].length; j++) {
                const x = j * simulation.gridSize;
                const y = i * simulation.gridSize;
                
                // 날개와의 상대 위치
                const dx = x - referenceX;
                const dy = y - referenceY;
                const distance = Math.sqrt(dx*dx + dy*dy);
                
                // 초기 유체 속도 (자유류)
                velocityField[i][j] = { u: U_inf, v: 0 };
                
                // 날개 형상에 근접한 점들만 계산 (성능 최적화)
                if (distance < simulation.chord * 2) {
                    // 날개와 포인트 사이 각도
                    const theta = Math.atan2(dy, dx);
                    
                    // 날개 형상 효과 계산
                    // 간소화된 포텐셜 흐름 모델
                    let angleFactor = 0;
                    
                    // 캠버와 받음각 효과
                    const effectiveAngle = (5 + simulation.flapDeflection * 0.3) * Math.PI / 180;
                    angleFactor = Math.sin(theta - effectiveAngle);
                    
                    // 두께 효과
                    const thicknessFactor = simulation.thickness / 100;
                    
                    // 속도 교란 계산 (단순화된 모델)
                    const distanceFactor = Math.min(1, simulation.chord / (distance + 0.1));
                    const velocityDisturbance = U_inf * angleFactor * distanceFactor * 
                                               (simulation.chord / 100) * 
                                               (1 + thicknessFactor * 2);
                    
                    // 플랩, 슬랫, 스포일러 효과 (생략)
                    
                    // 최종 속도 교란과 압력 계산 (생략)
                }
            }
        }
    }
    
    // 입자 위치 업데이트
    function updateParticles() {
        for (let p of simulation.particles) {
            // 현재 격자 위치 계산
            const i = Math.floor(p.y / simulation.gridSize);
            const j = Math.floor(p.x / simulation.gridSize);
            
            // 격자 내부에 있는지 확인
            if (i >= 0 && i < velocityField.length && j >= 0 && j < velocityField[0].length) {
                // 현재 위치의 속도 가져오기
                p.vx = velocityField[i][j].u;
                p.vy = velocityField[i][j].v;
            } else {
                // 기본 자유류 속도 사용
                p.vx = simulation.fluidVelocity;
                p.vy = 0;
            }
            
            // 입자 위치 업데이트
            p.x += p.vx * 0.2;
            p.y += p.vy * 0.2;
            p.age += 1;
            
            // 화면 밖으로 나간 입자 재배치
            if (p.x > canvas.width || p.x < 0 || p.y > canvas.height || p.y < 0 || p.age > 200) {
                p.x = Math.random() * 50;
                p.y = Math.random() * canvas.height;
                p.age = 0;
            }
        }
    }
    
    // 메인 시뮬레이션 렌더링 함수
    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 배경 그리기
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 압력장 렌더링
        renderPressureField();
        
        // 입자 및 속도 벡터 렌더링
        renderParticles();
        renderVelocityField();
        
        // 날개 형상 렌더링
        renderAirfoil();
        
        // 데이터 오버레이 렌더링
        renderDataOverlay();
    }
    // 시뮬레이션 업데이트 함수
    function updateSimulation() {
        calculateFlowField();
        updateParticles();
        render();
        
        if (simulation.running) {
            requestAnimationFrame(updateSimulation);
        }
    }
    
    // 시뮬레이션 초기화 및 시작
    function initSimulation() {
        generateAirfoilShape();
        initFluidGrid();
        initParticles();
        calculateFlowField();
        updateSimulation();
    }
    
    // 컨트롤 이벤트 리스너 설정
    function setupControls() {
        // 유체 속도 컨트롤 (m/s와 kt 단위)
        const velocityControl = document.getElementById('velocityControl');
        const velocityValue = document.getElementById('velocityValue');
        const velocityKtValue = document.getElementById('velocityKtValue');
        const velocityKtValue2 = document.getElementById('velocityKtValue2');
        
        if (velocityControl && velocityValue) {
            velocityControl.value = simulation.fluidVelocity;
            velocityValue.textContent = simulation.fluidVelocity.toFixed(1);
            
            // m/s에서 knot로 변환 (1 m/s = 1.94384 kt)
            if (velocityKtValue) {
                velocityKtValue.textContent = (simulation.fluidVelocity * 1.94384).toFixed(1);
            }
            if (velocityKtValue2) {
                velocityKtValue2.textContent = (simulation.fluidVelocity * 1.94384).toFixed(1);
            }
            
            velocityControl.addEventListener('input', function(e) {
                simulation.fluidVelocity = parseFloat(e.target.value);
                velocityValue.textContent = simulation.fluidVelocity.toFixed(1);
                
                // 노트 값 업데이트
                if (velocityKtValue) {
                    simulation.fluidVelocityKt = simulation.fluidVelocity * 1.94384;
                    velocityKtValue.textContent = simulation.fluidVelocityKt.toFixed(1);
                }
                if (velocityKtValue2) {
                    velocityKtValue2.textContent = simulation.fluidVelocityKt.toFixed(1);
                }
            });
        }
        
        // 노트 단위 속도 컨트롤
        const velocityKtControl = document.getElementById('velocityKtControl');
        
        if (velocityKtControl && velocityValue && velocityKtValue) {
            velocityKtControl.value = simulation.fluidVelocityKt;
            
            velocityKtControl.addEventListener('input', function(e) {
                simulation.fluidVelocityKt = parseFloat(e.target.value);
                if (velocityKtValue) {
                    velocityKtValue.textContent = simulation.fluidVelocityKt.toFixed(1);
                }
                if (velocityKtValue2) {
                    velocityKtValue2.textContent = simulation.fluidVelocityKt.toFixed(1);
                }
                
                // m/s 값 업데이트 (1 kt = 0.51444 m/s)
                simulation.fluidVelocity = simulation.fluidVelocityKt * 0.51444;
                velocityValue.textContent = simulation.fluidVelocity.toFixed(1);
                velocityControl.value = simulation.fluidVelocity;
            });
        }
        
        // 해발고도 및 기압 컨트롤
        const altitudeControl = document.getElementById('altitudeControl');
        const altitudeValue = document.getElementById('altitudeValue');
        const pressureValue = document.getElementById('pressureValue');
        
        if (altitudeControl && altitudeValue && pressureValue) {
            altitudeControl.value = simulation.altitude;
            altitudeValue.textContent = simulation.altitude.toFixed(0);
            
            altitudeControl.addEventListener('input', function(e) {
                simulation.altitude = parseFloat(e.target.value);
                altitudeValue.textContent = simulation.altitude.toFixed(0);
                
                // 해발고도에 따른 기압 계산 (국제표준대기 모델 사용)
                // P = P0 * (1 - 0.0065 * h / 288.15)^5.255
                if (simulation.altitude >= 0 && simulation.altitude <= 11000) {
                    simulation.fluidPressure = 101.325 * Math.pow(1 - (0.0065 * simulation.altitude / 288.15), 5.255);
                } else if (simulation.altitude > 11000 && simulation.altitude <= 20000) {
                    // 11km부터 20km까지는 다른 모델 사용
                    const p11km = 22.632; // 11km에서의 압력 (kPa)
                    simulation.fluidPressure = p11km * Math.exp(-0.1577 * (simulation.altitude - 11000) / 1000);
                }
                
                pressureValue.textContent = simulation.fluidPressure.toFixed(1);
                
                // 고도에 따른 밀도 재계산
                updateAirDensity();
            });
        }
        
        // 기압 직접 제어 (고급 모드)
        const pressureControl = document.getElementById('pressureControl');
        
        if (pressureControl && pressureValue) {
            pressureControl.value = simulation.fluidPressure;
            pressureValue.textContent = simulation.fluidPressure.toFixed(1);
            
            pressureControl.addEventListener('input', function(e) {
                simulation.fluidPressure = parseFloat(e.target.value);
                pressureValue.textContent = simulation.fluidPressure.toFixed(1);
                
                // 기압에 따른 고도 역계산 (간단한 근사 - 정확도는 낮음)
                if (simulation.fluidPressure > 22.632) {
                    // 0-11km 고도 범위
                    simulation.altitude = ((1 - Math.pow(simulation.fluidPressure / 101.325, 1/5.255)) * 288.15) / 0.0065;
                } else {
                    // 11-20km 고도 범위
                    simulation.altitude = 11000 - (Math.log(simulation.fluidPressure / 22.632) / 0.1577) * 1000;
                }
                
                if (altitudeControl && altitudeValue) {
                    altitudeControl.value = simulation.altitude;
                    altitudeValue.textContent = simulation.altitude.toFixed(0);
                }
                
                // 밀도 재계산
                updateAirDensity();
            });
        }
        
        // 유체 온도 컨트롤
        const temperatureControl = document.getElementById('temperatureControl');
        const temperatureValue = document.getElementById('temperatureValue');
        
        if (temperatureControl && temperatureValue) {
            temperatureControl.value = simulation.fluidTemperature;
            temperatureValue.textContent = simulation.fluidTemperature.toFixed(1);
            
            temperatureControl.addEventListener('input', function(e) {
                simulation.fluidTemperature = parseFloat(e.target.value);
                temperatureValue.textContent = simulation.fluidTemperature.toFixed(1);
                
                // 온도 변화에 따른 공기 밀도 재계산
                updateAirDensity();
            });
        }
        
        // 플랩, 슬랫, 스포일러 컨트롤 (코드 생략)
        // ...
        
        // 시각화 옵션 컨트롤
        const pressureToggle = document.getElementById('pressureToggle');
        const particlesToggle = document.getElementById('particlesToggle');
        const vectorsToggle = document.getElementById('vectorsToggle');
        
        if (pressureToggle) {
            pressureToggle.checked = simulation.showPressure;
            pressureToggle.addEventListener('change', function(e) {
                simulation.showPressure = e.target.checked;
            });
        }
        
        if (particlesToggle) {
            particlesToggle.checked = simulation.showParticles;
            particlesToggle.addEventListener('change', function(e) {
                simulation.showParticles = e.target.checked;
            });
        }
        
        if (vectorsToggle) {
            vectorsToggle.checked = simulation.showVectors;
            vectorsToggle.addEventListener('change', function(e) {
                simulation.showVectors = e.target.checked;
            });
        }
        
        // 시뮬레이션 제어 버튼
        const startButton = document.getElementById('startSimulation');
        const stopButton = document.getElementById('stopSimulation');
        const resetButton = document.getElementById('resetSimulation');
        
        if (startButton) {
            startButton.addEventListener('click', function() {
                if (!simulation.running) {
                    simulation.running = true;
                    updateSimulation();
                }
            });
        }
        
        if (stopButton) {
            stopButton.addEventListener('click', function() {
                simulation.running = false;
            });
        }
        
        if (resetButton) {
            resetButton.addEventListener('click', function() {
                // 날개 설정 초기화
                simulation.flapDeflection = 0;
                simulation.slatExtension = 0;
                simulation.spoilerDeflection = 0;
                
                // 컨트롤 업데이트
                if (flapControl && flapValue) {
                    flapControl.value = simulation.flapDeflection;
                    flapValue.textContent = simulation.flapDeflection.toFixed(1);
                }
                
                if (slatControl && slatValue) {
                    slatControl.value = simulation.slatExtension;
                    slatValue.textContent = simulation.slatExtension.toFixed(1);
                }
                
                if (spoilerControl && spoilerValue) {
                    spoilerControl.value = simulation.spoilerDeflection;
                    spoilerValue.textContent = simulation.spoilerDeflection.toFixed(1);
                }
                
                // 시뮬레이션 재초기화
                initSimulation();
            });
        }
    }
    
    // 초기화 및 시뮬레이션 시작
    setupControls();
    initSimulation();
});