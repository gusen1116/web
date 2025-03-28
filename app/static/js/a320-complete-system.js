/**
 * precise-a320-airfoil.js - 정밀한 A320 날개 시스템 시뮬레이션
 * 실제 항공기 데이터 기반 초임계 에어포일 및 고양력 장치 구현
 */

document.addEventListener('DOMContentLoaded', function() {
    // 캔버스 및 컨텍스트 설정
    const canvas = document.getElementById('airfoilCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 캔버스 크기 설정
    function resizeCanvas() {
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = 600;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // A320 날개 및 고양력 장치 파라미터
    const simulation = {
        // 날개 기본 형상
        chord: 450,              // 날개 시위 길이 (픽셀)
        thickness: 11.5,         // 날개 두께 (시위의 %) - A320 초임계 에어포일
        camber: 1.2,             // 캠버 (시위의 %)
        angleOfAttack: -5.0,     // 받음각 (도)
        
        // A320 플랩 설정 
        flapDeflection: 20,      // 플랩 각도 (도): 0, 10, 15, 20, 35, 40
        flapPosition: "3",       // 플랩 위치 텍스트: UP, 1, 2, 3, FULL
        flapLength: 30,          // 플랩 길이 (시위의 %)
        
        // A320 슬랫 설정
        slatExtension: 25,       // 슬랫 확장 (%): 0, 18, 22, 24, 26
        slatPosition: "3",       // 슬랫 위치 텍스트: UP, MID, 1, 2, 3
        slatLength: 15,          // 슬랫 길이 (시위의 %)
        
        // A320 스포일러 설정
        spoilerDeflection: 0,    // 스포일러 각도 (도): 0-50
        spoilerPanels: 5,        // 스포일러 패널 수
        
        // 시각화 매개변수
        fluidVelocity: 10,       // 자유 유동 속도 (m/s)
        gridSize: 3,             // 그리드 크기 (픽셀) - 더 조밀하게
        streamlineDensity: 4,    // 유선 밀도 - 더 촘촘하게
        particleCount: 400,      // 입자 수 - 더 많이
        particles: [],
        
        // 유동장 데이터
        pressureField: [],
        velocityField: [],
        
        // 시뮬레이션 상태
        running: true,
        showPressure: true,      // 압력 분포 표시
        showStreamlines: true,   // 유선 표시
        showVectors: false,      // 속도 벡터 표시
        
        // 압력 색상 매핑 범위
        minPressure: -1.0,
        maxPressure: 1.0,
        
        // 좌표계 방향
        flowDirection: 'left-to-right', // 'left-to-right' 또는 'right-to-left'
    };
    
    // 날개 형상 데이터
    let mainWingPoints = [];     // 메인 날개 포인트 (슬랫, 플랩 제외)
    let slatPoints = [];         // 슬랫 포인트
    let flapPoints = [];         // 플랩 포인트
    let spoilerPoints = [];      // 스포일러 포인트 (상부 표면에만 존재)
    
    // 좌표 변환 함수 (방향 설정에 따라 조정)
    function transformX(x) {
        if (simulation.flowDirection === 'left-to-right') {
            return (x / 100 * simulation.chord) + canvas.width * 0.25;
        } else {
            return canvas.width - ((x / 100 * simulation.chord) + canvas.width * 0.25);
        }
    }
    
    function transformY(y) {
        return canvas.height / 2 - (y / 100 * simulation.chord);
    }
    
    // 압력 계수를 색상으로 매핑 (개선된 CFD 스타일)
    function getPressureColor(cp) {
        // 압력 값을 0-1 범위로 정규화
        const normalizedValue = (cp - simulation.minPressure) / 
                              (simulation.maxPressure - simulation.minPressure);
        
        // 중간값이 녹색인 개선된 Jet 색상 맵
        let r, g, b;
        
        if (normalizedValue < 0.2) {
            // 파란색에서 청록색으로
            const t = normalizedValue / 0.2;
            r = 0;
            g = Math.round(150 * t);
            b = 255;
        } else if (normalizedValue < 0.5) {
            // 청록색에서 녹색으로
            const t = (normalizedValue - 0.2) / 0.3;
            r = 0;
            g = Math.round(150 + 105 * t);
            b = Math.round(255 * (1 - t));
        } else if (normalizedValue < 0.8) {
            // 녹색에서 노란색으로
            const t = (normalizedValue - 0.5) / 0.3;
            r = Math.round(255 * t);
            g = 255;
            b = 0;
        } else {
            // 노란색에서 빨간색으로
            const t = (normalizedValue - 0.8) / 0.2;
            r = 255;
            g = Math.round(255 * (1 - t));
            b = 0;
        }
        
        return `rgb(${r}, ${g}, ${b})`;
    }
    
    // A320 초임계 에어포일 및 고양력 장치 형상 생성
    function generateAirfoilShape() {
        // 각 부분 초기화
        mainWingPoints = [];
        slatPoints = [];
        flapPoints = [];
        spoilerPoints = [];
        
        // 초임계 에어포일 매개변수 
        const t = simulation.thickness / 100;  // 두께 비율
        
        // 기준점 설정
        const slatEndPos = simulation.slatLength;           // 슬랫 종료 위치 (%)
        const flapStartPos = 100 - simulation.flapLength;   // 플랩 시작 위치 (%)
        
        // 스포일러 위치 설정 (상부 표면에만)
        const spoilerStartPos = 35;  // 날개 앞쪽에서 35% 위치에서 시작
        const spoilerEndPos = 70;    // 날개 앞쪽에서 70% 위치에서 종료
        
        // A320 플랩 설정에 따른 실제 각도 및 변위
        let flapAngle, flapTranslationX, flapTranslationY, flapSlotSize;
        
        // 플랩 설정에 따른 값
        switch(simulation.flapPosition) {
            case "UP":  // 수납
                flapAngle = 0;
                flapTranslationX = 0;
                flapTranslationY = 0;
                flapSlotSize = 0;
                break;
            case "1":  // 이륙1 (10°)
                flapAngle = 10;
                flapTranslationX = 2;  // 시위의 2% 뒤로 이동
                flapTranslationY = -0.5; // 시위의 0.5% 아래로 이동 (음수 = 아래로)
                flapSlotSize = 0.5;
                break;
            case "2":  // 이륙2 (15°)
                flapAngle = 15;
                flapTranslationX = 3.5;
                flapTranslationY = -1;
                flapSlotSize = 1;
                break;
            case "3":  // 이륙3 (20°)
                flapAngle = 20;
                flapTranslationX = 5;
                flapTranslationY = -2;
                flapSlotSize = 1.5;
                break;
            case "FULL":  // 착륙 (35° or 40°)
                if (simulation.flapDeflection <= 35) {
                    flapAngle = 35;
                    flapTranslationX = 8;
                    flapTranslationY = -4;
                    flapSlotSize = 2;
                } else {
                    flapAngle = 40;
                    flapTranslationX = 10;
                    flapTranslationY = -5;
                    flapSlotSize = 2.5;
                }
                break;
            default:
                flapAngle = 0;
                flapTranslationX = 0;
                flapTranslationY = 0;
                flapSlotSize = 0;
        }
        
        // A320 슬랫 설정에 따른 확장 값
        let slatExtension, slatDropDistance;
        
        // 슬랫 설정에 따른 값
        switch(simulation.slatPosition) {
            case "UP":  // 수납
                slatExtension = 0;
                slatDropDistance = 0;
                break;
            case "MID":  // 중간 (S 위치)
                slatExtension = 18;
                slatDropDistance = 1;
                break;
            case "1":  // 설정 1
                slatExtension = 22;
                slatDropDistance = 1.5;
                break;
            case "2":  // 설정 2
                slatExtension = 24;
                slatDropDistance = 2;
                break;
            case "3":  // 완전 확장
                slatExtension = 26;
                slatDropDistance = 3;
                break;
            default:
                slatExtension = 0;
                slatDropDistance = 0;
        }
        
        // 라디안으로 변환
        const flapAngleRad = flapAngle * Math.PI / 180;
        
        // 더 많은 점으로 더 부드러운 형상
        const numPoints = 300;
        
        // 1. 슬랫 생성 (날개 앞부분)
        if (simulation.slatPosition !== "UP") {
            for (let i = 0; i <= numPoints / 6; i++) {
                const t = i / (numPoints / 6);
                const x = t * slatEndPos;
                
                // A320 초임계 에어포일 형상 - 슬랫 부분
                // 슬랫은 앞부분 형상과 유사하나 약간 더 얇고 곡률이 있음
                const xc = x / 100; // 0-1 범위의 x
                
                // 수정된 두께 분포 (앞전 부분 강화)
                let yt = t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
                
                // 슬랫은 특수한 캠버라인을 가짐
                let yc = 0.1 * xc * (1 - xc); // 간단한 캠버라인
                
                // 두께는 원래 날개보다 약간 얇게
                yt *= 0.9 * simulation.thickness;
                
                // 상부 및 하부 좌표
                const yu = yc + yt;
                const yl = yc - yt * 0.7; // 하부는 더 평평하게
                
                // 슬랫 이동 적용 (앞으로 및 약간 아래로)
                const slatExtensionPercent = slatExtension / 100;
                const offsetX = -slatEndPos * slatExtensionPercent * 0.5;
                const offsetY = -slatDropDistance; // 음수 = 아래로
                
                slatPoints.push({
                    x: x + offsetX,
                    yu: yu + offsetY,
                    yl: yl + offsetY
                });
            }
        }
        
        // 2. 메인 날개 부분 (슬랫과 플랩 사이)
        // 초임계 에어포일 구현을 위한 좌표 준비
        const mainWingStart = simulation.slatPosition !== "UP" ? slatEndPos * 0.8 : 0;
        
        for (let i = 0; i <= numPoints; i++) {
            const t = i / numPoints;
            const x = mainWingStart + t * (flapStartPos - mainWingStart);
            
            // A320 초임계 에어포일 형상
            const xc = x / 100; // 0-1 범위의 x
            
            // 초임계 에어포일 두께 분포 - 상부가 더 평평하도록 수정
            let yt;
            if (xc < 0.3) {
                // 앞부분은 일반 NACA 형상과 유사
                yt = t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
            } else {
                // 중간~뒷부분은 상부가 더 평평한 초임계 형상
                yt = t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
                
                // 상부 평평화 추가 보정
                if (x > 30 && x < 70) {
                    yt *= (1 - 0.1 * Math.sin((x - 30) / 40 * Math.PI));
                }
            }
            
            // 초임계 에어포일 캠버 - 앞쪽으로 약간 이동
            const p = 0.35; // 최대 캠버 위치 (일반 에어포일보다 앞쪽)
            const m = simulation.camber / 100;
            
            let yc;
            if (xc <= p) {
                yc = m * (xc / p**2) * (2 * p - xc);
            } else {
                yc = m * ((1 - xc) / (1 - p)**2) * (1 + xc - 2 * p);
            }
            
            // 두께 조정 (초임계 에어포일 특성)
            yt *= simulation.thickness;
            
            // 상부 및 하부 표면 좌표
            const yu = yc + yt;
            const yl = yc - yt * 0.8; // 하부는 좀 더 평평하게
            
            mainWingPoints.push({
                x: x,
                yu: yu,
                yl: yl,
                isSpStart: x >= spoilerStartPos && x < spoilerStartPos + 1,
                isSpEnd: x >= spoilerEndPos - 1 && x < spoilerEndPos
            });
            
            // 스포일러 위치 체크 및 생성 (상부 표면에만)
            if (x >= spoilerStartPos && x <= spoilerEndPos && simulation.spoilerDeflection > 0) {
                // 스포일러 패널로 분할
                const panelWidth = (spoilerEndPos - spoilerStartPos) / simulation.spoilerPanels;
                const panelIndex = Math.floor((x - spoilerStartPos) / panelWidth);
                const panelPosition = (x - (spoilerStartPos + panelIndex * panelWidth)) / panelWidth;
                
                // 각 패널의 중앙에서 최대 전개
                const peakPosition = 0.5;
                const deflectionFactor = 1 - Math.abs(panelPosition - peakPosition) * 2;
                
                // 스포일러 각도에 따른 높이 계산
                const spoilerHeight = (simulation.spoilerDeflection / 50) * 10 * deflectionFactor;
                
                if (spoilerHeight > 0) {
                    spoilerPoints.push({
                        x: x,
                        y: yu,
                        height: spoilerHeight,
                        panelIndex: panelIndex
                    });
                }
            }
        }
        
        // 3. 플랩 부분 생성 (파울러 플랩 메커니즘)
        if (simulation.flapPosition !== "UP") {
            for (let i = 0; i <= numPoints / 3; i++) {
                const t = i / (numPoints / 3);
                const xRel = t * simulation.flapLength;
                const x = flapStartPos + xRel;
                
                // 플랩용 에어포일 형상 (메인 날개보다 단순화된 형상)
                const xc = xRel / simulation.flapLength; // 0-1 범위로 정규화
                
                // 플랩 두께 분포 - 뒤로 갈수록 얇아짐
                let yt = t * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4);
                
                // 플랩 테이퍼링 (뒤로 갈수록 얇아짐)
                const taperFactor = 1 - (xRel / simulation.flapLength) * 0.7;
                yt *= taperFactor;
                
                // 간단한 캠버라인
                const yc = simulation.camber / 200 * Math.sin(Math.PI * xc);
                
                // 두께 조정
                yt *= simulation.thickness * 0.8; // 플랩은 메인 날개보다 약간 얇음
                
                // 상부 및 하부 좌표
                const yu = yc + yt;
                const yl = yc - yt * 0.8; // 하부는 좀 더 평평하게
                
                // 플랩 변환 적용
                // 1. 뒤로 이동 (translation)
                const xTranslated = xRel + flapTranslationX;
                const yuTranslated = yu + flapTranslationY; // 아래로 이동 (음수)
                const ylTranslated = yl + flapTranslationY;
                
                // 2. 회전 (rotation around hinge)
                // 플랩 힌지 중심 좌표
                const hingeX = 0;
                const hingeY = 0;
                
                // 회전 행렬 적용
                const sinA = Math.sin(flapAngleRad);
                const cosA = Math.cos(flapAngleRad);
                
                const xRotated = cosA * (xTranslated - hingeX) - sinA * (yuTranslated - hingeY) + hingeX;
                const yuRotated = sinA * (xTranslated - hingeX) + cosA * (yuTranslated - hingeY) + hingeY;
                const ylRotated = sinA * (xTranslated - hingeX) + cosA * (ylTranslated - hingeY) + hingeY;
                
                // 전체 좌표계로 변환
                const xFinal = flapStartPos + xRotated;
                const yuFinal = yuRotated;
                const ylFinal = ylRotated;
                
                flapPoints.push({
                    x: xFinal,
                    yu: yuFinal,
                    yl: ylFinal,
                    isLeadingEdge: i === 0
                });
            }
        }
    }
    
    // 유동 계산 (개선된 알고리즘)
    function calculateFlow() {
        // 격자 크기 계산
        const gridRows = Math.ceil(canvas.height / simulation.gridSize);
        const gridCols = Math.ceil(canvas.width / simulation.gridSize);
        
        // 받음각 (라디안)
        const alphaRad = simulation.angleOfAttack * Math.PI / 180;
        
        // 압력장 및 속도장 초기화
        simulation.pressureField = new Array(gridRows);
        simulation.velocityField = new Array(gridRows);
        
        for (let i = 0; i < gridRows; i++) {
            simulation.pressureField[i] = new Array(gridCols);
            simulation.velocityField[i] = new Array(gridCols);
            
            for (let j = 0; j < gridCols; j++) {
                // 초기 자유류 속도 (받음각 적용)
                let u, v;
                
                if (simulation.flowDirection === 'left-to-right') {
                    u = simulation.fluidVelocity * Math.cos(alphaRad);
                    v = simulation.fluidVelocity * Math.sin(alphaRad);
                } else {
                    u = -simulation.fluidVelocity * Math.cos(alphaRad);
                    v = simulation.fluidVelocity * Math.sin(alphaRad);
                }
                
                simulation.velocityField[i][j] = { u, v };
                simulation.pressureField[i][j] = 0;
            }
        }
        
        // 기준점 (1/4 시위점)
        const referenceX = simulation.flowDirection === 'left-to-right' 
            ? canvas.width * 0.25 + simulation.chord * 0.25
            : canvas.width * 0.75 - simulation.chord * 0.25;
        const referenceY = canvas.height / 2;
        
        // 패널 메소드 기반 계산
        const panelPoints = [];
        
        // 메인 날개, 슬랫, 플랩의 모든 점을 통합
        if (mainWingPoints.length > 0) {
            // 상부 표면
            for (let i = 0; i < mainWingPoints.length; i++) {
                panelPoints.push({
                    x: transformX(mainWingPoints[i].x),
                    y: transformY(mainWingPoints[i].yu)
                });
            }
            
            // 하부 표면 (역순)
            for (let i = mainWingPoints.length - 1; i >= 0; i--) {
                panelPoints.push({
                    x: transformX(mainWingPoints[i].x),
                    y: transformY(mainWingPoints[i].yl)
                });
            }
        }
        
        if (slatPoints.length > 0) {
            // 슬랫 추가
            const offset = panelPoints.length;
            
            // 상부 표면
            for (let i = 0; i < slatPoints.length; i++) {
                panelPoints.push({
                    x: transformX(slatPoints[i].x),
                    y: transformY(slatPoints[i].yu)
                });
            }
            
            // 하부 표면 (역순)
            for (let i = slatPoints.length - 1; i >= 0; i--) {
                panelPoints.push({
                    x: transformX(slatPoints[i].x),
                    y: transformY(slatPoints[i].yl)
                });
            }
        }
        
        if (flapPoints.length > 0) {
            // 플랩 추가
            const offset = panelPoints.length;
            
            // 상부 표면
            for (let i = 0; i < flapPoints.length; i++) {
                panelPoints.push({
                    x: transformX(flapPoints[i].x),
                    y: transformY(flapPoints[i].yu)
                });
            }
            
            // 하부 표면 (역순)
            for (let i = flapPoints.length - 1; i >= 0; i--) {
                panelPoints.push({
                    x: transformX(flapPoints[i].x),
                    y: transformY(flapPoints[i].yl)
                });
            }
        }
        
        // 각 그리드 점에서 유동 교란 계산
        for (let i = 0; i < gridRows; i++) {
            for (let j = 0; j < gridCols; j++) {
                const x = j * simulation.gridSize;
                const y = i * simulation.gridSize;
                
                // 기준점 기준 상대 좌표
                const dx = x - referenceX;
                const dy = y - referenceY;
                const r = Math.sqrt(dx*dx + dy*dy);
                
                // 날개에 너무 가까운 점은 건너뜀
                if (r < 0.03 * simulation.chord) continue;
                
                // 점이 날개 내부인지 확인 (단순화된 체크)
                let isInside = false;
                
                // 기존 속도 가져오기
                let u = simulation.velocityField[i][j].u;
                let v = simulation.velocityField[i][j].v;
                
                // 받음각에 의한 순환 (양력)
                const circulation = Math.abs(simulation.angleOfAttack) * Math.PI / 180 * 
                                  simulation.fluidVelocity * simulation.chord * 
                                  (1 + (simulation.flapDeflection / 40) * 0.3);
                
                // 유동 교란 계산 (패널 메소드 간소화)
                // 1. 두께 효과 + 캠버 효과
                const theta = Math.atan2(dy, dx);
                const thicknessEffect = simulation.thickness * simulation.fluidVelocity * 0.05 / r;
                
                u += thicknessEffect * Math.cos(theta);
                v += thicknessEffect * Math.sin(theta);
                
                // 2. 받음각 효과 (보텍스)
                const circulationEffect = circulation / (2 * Math.PI * r);
                
                if (simulation.flowDirection === 'left-to-right') {
                    u -= circulationEffect * Math.sin(theta);
                    v += circulationEffect * Math.cos(theta);
                } else {
                    u += circulationEffect * Math.sin(theta);
                    v += circulationEffect * Math.cos(theta);
                }
                
                // 3. 고양력 장치 효과 (추가 보텍스 및 소스)
                // 3.1 슬랫 효과
                if (simulation.slatPosition !== "UP") {
                    const slatX = simulation.flowDirection === 'left-to-right'
                        ? referenceX - simulation.chord * 0.4
                        : referenceX + simulation.chord * 0.4;
                    const slatY = referenceY;
                    const dxSlat = x - slatX;
                    const dySlat = y - slatY;
                    const rSlat = Math.sqrt(dxSlat*dxSlat + dySlat*dySlat);
                    
                    if (rSlat > 0.03 * simulation.chord) {
                        // 슬랫 유동 교란
                        const slatCirculation = (parseInt(simulation.slatExtension) / 100) * 
                                             simulation.fluidVelocity * simulation.chord * 0.15;
                        const slatEffect = slatCirculation / (2 * Math.PI * rSlat);
                        const thetaSlat = Math.atan2(dySlat, dxSlat);
                        
                        if (simulation.flowDirection === 'left-to-right') {
                            u -= slatEffect * Math.sin(thetaSlat);
                            v += slatEffect * Math.cos(thetaSlat);
                        } else {
                            u += slatEffect * Math.sin(thetaSlat);
                            v += slatEffect * Math.cos(thetaSlat);
                        }
                    }
                }
                
                // 3.2 플랩 효과
                if (simulation.flapPosition !== "UP") {
                    const flapX = simulation.flowDirection === 'left-to-right'
                        ? referenceX + simulation.chord * 0.4
                        : referenceX - simulation.chord * 0.4;
                    const flapY = referenceY + simulation.chord * 0.05; // 약간 아래쪽
                    const dxFlap = x - flapX;
                    const dyFlap = y - flapY;
                    const rFlap = Math.sqrt(dxFlap*dxFlap + dyFlap*dyFlap);
                    
                    if (rFlap > 0.03 * simulation.chord) {
                        // 플랩 유동 교란
                        const flapCirculation = (simulation.flapDeflection / 40) * 
                                             simulation.fluidVelocity * simulation.chord * 0.4;
                        const flapEffect = flapCirculation / (2 * Math.PI * rFlap);
                        const thetaFlap = Math.atan2(dyFlap, dxFlap);
                        
                        if (simulation.flowDirection === 'left-to-right') {
                            u -= flapEffect * Math.sin(thetaFlap);
                            v += flapEffect * Math.cos(thetaFlap);
                        } else {
                            u += flapEffect * Math.sin(thetaFlap);
                            v += flapEffect * Math.cos(thetaFlap);
                        }
                    }
                }
                
                // 3.3 스포일러 효과
                if (simulation.spoilerDeflection > 0) {
                    const spoilerX = simulation.flowDirection === 'left-to-right'
                        ? referenceX + simulation.chord * 0.05
                        : referenceX - simulation.chord * 0.05;
                    const spoilerY = referenceY - simulation.chord * 0.05; // 상부 표면
                    const dxSpoiler = x - spoilerX;
                    const dySpoiler = y - spoilerY;
                    const rSpoiler = Math.sqrt(dxSpoiler*dxSpoiler + dySpoiler*dySpoiler);
                    
                    if (rSpoiler > 0.03 * simulation.chord) {
                        // 스포일러 역효과 (양력 감소, 항력 증가)
                        const spoilerEffect = (simulation.spoilerDeflection / 50) * 
                                           simulation.fluidVelocity * 0.3 / rSpoiler;
                        const thetaSpoiler = Math.atan2(dySpoiler, dxSpoiler);
                        
                        // 스포일러 뒤에서 속도 감소
                        const isDownstream = simulation.flowDirection === 'left-to-right' 
                            ? x > spoilerX : x < spoilerX;
                        
                        if (isDownstream && Math.abs(y - spoilerY) < simulation.chord * 0.25) {
                            if (simulation.flowDirection === 'left-to-right') {
                                u -= spoilerEffect * Math.abs(Math.cos(thetaSpoiler));
                                v -= spoilerEffect * Math.abs(Math.sin(thetaSpoiler)) * 0.5;
                            } else {
                                u += spoilerEffect * Math.abs(Math.cos(thetaSpoiler));
                                v -= spoilerEffect * Math.abs(Math.sin(thetaSpoiler)) * 0.5;
                            }
                        }
                    }
                }
                
                // 속도 업데이트
                simulation.velocityField[i][j].u = u;
                simulation.velocityField[i][j].v = v;
                
                // 압력 계수 계산 (베르누이 방정식)
                const speedSq = u*u + v*v;
                const freeStreamSpeedSq = simulation.fluidVelocity * simulation.fluidVelocity;
                
                // Cp = 1 - (v/v∞)²
                const pressureCoefficient = 1 - (speedSq / freeStreamSpeedSq);
                simulation.pressureField[i][j] = pressureCoefficient;
            }
        }
    }
    
    // 유선 시각화를 위한 입자 초기화
    function initParticles() {
        simulation.particles = [];
        
        // 균일한 분포의 입자 생성
        for (let i = 0; i < simulation.particleCount; i++) {
            const yPos = canvas.height * 0.1 + (canvas.height * 0.8) * (i / simulation.particleCount);
            
            let xPos;
            if (simulation.flowDirection === 'left-to-right') {
                xPos = Math.random() * canvas.width * 0.15; // 왼쪽에서 시작
            } else {
                xPos = canvas.width - Math.random() * canvas.width * 0.15; // 오른쪽에서 시작
            }
            
            simulation.particles.push({
                x: xPos,
                y: yPos,
                age: Math.random() * 50,
                path: []
            });
        }
    }
    
    // 입자 위치 업데이트
    function updateParticles() {
        const alphaRad = simulation.angleOfAttack * Math.PI / 180;
        let defaultU, defaultV;
        
        if (simulation.flowDirection === 'left-to-right') {
            defaultU = simulation.fluidVelocity * Math.cos(alphaRad);
            defaultV = simulation.fluidVelocity * Math.sin(alphaRad);
        } else {
            defaultU = -simulation.fluidVelocity * Math.cos(alphaRad);
            defaultV = simulation.fluidVelocity * Math.sin(alphaRad);
        }
        
        for (let p of simulation.particles) {
            // 그리드 인덱스 계산
            const i = Math.floor(p.y / simulation.gridSize);
            const j = Math.floor(p.x / simulation.gridSize);
            
            // 기본 속도 (자유류)
            let u = defaultU;
            let v = defaultV;
            
            // 그리드 내에 있으면 계산된 속도 사용
            if (i >= 0 && i < simulation.velocityField.length && 
                j >= 0 && j < simulation.velocityField[0].length) {
                if (simulation.velocityField[i][j]) {
                    u = simulation.velocityField[i][j].u;
                    v = simulation.velocityField[i][j].v;
                }
            }
            
            // 경로 저장 (유선 표시용)
            if (p.path.length > 150) {
                p.path.shift(); // 오래된 점 제거
            }
            p.path.push({x: p.x, y: p.y});
            
            // 입자 위치 업데이트 
            const timeStep = 0.2;
            p.x += u * timeStep;
            p.y += v * timeStep;
            p.age += 1;
            
            // 화면 밖으로 나가거나 오래된 경우 재설정
            if (p.x < 0 || p.x > canvas.width || 
                p.y < 0 || p.y > canvas.height || 
                p.age > 300) {
                
                const yPos = canvas.height * 0.1 + (canvas.height * 0.8) * (Math.random());
                
                if (simulation.flowDirection === 'left-to-right') {
                    p.x = Math.random() * canvas.width * 0.15; // 왼쪽에서 시작
                } else {
                    p.x = canvas.width - Math.random() * canvas.width * 0.15; // 오른쪽에서 시작
                }
                
                p.y = yPos;
                p.age = 0;
                p.path = [];
            }
        }
    }
    
    // 압력장 렌더링 (더 부드러운 그라데이션)
    function renderPressureField() {
        if (!simulation.showPressure) return;
        
        const imgData = ctx.createImageData(canvas.width, canvas.height);
        const data = imgData.data;
        
        for (let i = 0; i < simulation.pressureField.length; i++) {
            for (let j = 0; j < simulation.pressureField[i].length; j++) {
                if (simulation.pressureField[i][j] === undefined) continue;
                
                const cp = simulation.pressureField[i][j];
                const color = getPressureColor(cp);
                
                // RGB 색상 추출
                const r = parseInt(color.substring(4, color.indexOf(',')));
                const g = parseInt(color.substring(color.indexOf(',') + 1, color.lastIndexOf(',')));
                const b = parseInt(color.substring(color.lastIndexOf(',') + 1, color.indexOf(')')));
                
                // 그리드 셀 채우기
                for (let y = i * simulation.gridSize; y < (i + 1) * simulation.gridSize; y++) {
                    for (let x = j * simulation.gridSize; x < (j + 1) * simulation.gridSize; x++) {
                        if (x < canvas.width && y < canvas.height) {
                            const pos = (y * canvas.width + x) * 4;
                            data[pos] = r;
                            data[pos + 1] = g;
                            data[pos + 2] = b;
                            data[pos + 3] = 250; // 거의 불투명
                        }
                    }
                }
            }
        }
        
        ctx.putImageData(imgData, 0, 0);
    }
    
    // 유선 렌더링 (더 부드럽고 오래 지속)
    function renderStreamlines() {
        if (!simulation.showStreamlines) return;
        
        // 각 입자의 경로를 유선으로 그리기
        for (const p of simulation.particles) {
            if (p.path.length < 2) continue;
            
            // 유선 그라데이션 효과 (앞쪽은 밝게, 뒤쪽은 흐리게)
            const gradient = ctx.createLinearGradient(
                p.path[0].x, p.path[0].y, 
                p.path[p.path.length - 1].x, p.path[p.path.length - 1].y
            );
            
            if (simulation.flowDirection === 'left-to-right') {
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0.1)');
                gradient.addColorStop(1, 'rgba(255, 255, 255, 0.8)');
            } else {
                gradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
                gradient.addColorStop(1, 'rgba(255, 255, 255, 0.1)');
            }
            
            ctx.beginPath();
            ctx.strokeStyle = gradient;
            ctx.lineWidth = 1;
            
            ctx.moveTo(p.path[0].x, p.path[0].y);
            
            // 경로를 부드럽게 연결 (베지어 곡선 사용)
            for (let i = 1; i < p.path.length - 2; i++) {
                const xc = (p.path[i].x + p.path[i + 1].x) / 2;
                const yc = (p.path[i].y + p.path[i + 1].y) / 2;
                ctx.quadraticCurveTo(p.path[i].x, p.path[i].y, xc, yc);
            }
            
            // 마지막 두 점 처리
            if (p.path.length > 2) {
                ctx.quadraticCurveTo(
                    p.path[p.path.length - 2].x,
                    p.path[p.path.length - 2].y,
                    p.path[p.path.length - 1].x,
                    p.path[p.path.length - 1].y
                );
            }
            
            ctx.stroke();
        }
        
        // 현재 입자 위치 표시 (더 작고 투명하게)
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        for (const p of simulation.particles) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 0.8, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    // 메인 날개 렌더링
    function renderMainWing() {
        if (mainWingPoints.length <= 1) return;
        
        ctx.beginPath();
        
        // 상부 표면
        ctx.moveTo(transformX(mainWingPoints[0].x), transformY(mainWingPoints[0].yu));
        
        for (let i = 1; i < mainWingPoints.length; i++) {
            ctx.lineTo(transformX(mainWingPoints[i].x), transformY(mainWingPoints[i].yu));
        }
        
        // 하부 표면 (뒤에서부터)
        for (let i = mainWingPoints.length - 1; i >= 0; i--) {
            ctx.lineTo(transformX(mainWingPoints[i].x), transformY(mainWingPoints[i].yl));
        }
        
        ctx.closePath();
        
        // 메인 날개 스타일 (약간 회색빛 흰색)
        ctx.fillStyle = '#e8e8e8';
        ctx.strokeStyle = '#606060';
        ctx.lineWidth = 1;
        ctx.fill();
        ctx.stroke();
    }
    
    // 슬랫 렌더링
    function renderSlat() {
        if (slatPoints.length <= 1) return;
        
        ctx.beginPath();
        
        // 상부 표면
        ctx.moveTo(transformX(slatPoints[0].x), transformY(slatPoints[0].yu));
        
        for (let i = 1; i < slatPoints.length; i++) {
            ctx.lineTo(transformX(slatPoints[i].x), transformY(slatPoints[i].yu));
        }
        
        // 하부 표면 (뒤에서부터)
        for (let i = slatPoints.length - 1; i >= 0; i--) {
            ctx.lineTo(transformX(slatPoints[i].x), transformY(slatPoints[i].yl));
        }
        
        ctx.closePath();
        
        // 슬랫 스타일 (약간 더 어두운 회색)
        ctx.fillStyle = '#d8d8d8';
        ctx.strokeStyle = '#606060';
        ctx.lineWidth = 1;
        ctx.fill();
        ctx.stroke();
    }
    
    // 플랩 렌더링
    function renderFlap() {
        if (flapPoints.length <= 1) return;
        
        ctx.beginPath();
        
        // 상부 표면
        ctx.moveTo(transformX(flapPoints[0].x), transformY(flapPoints[0].yu));
        
        for (let i = 1; i < flapPoints.length; i++) {
            ctx.lineTo(transformX(flapPoints[i].x), transformY(flapPoints[i].yu));
        }
        
        // 하부 표면 (뒤에서부터)
        for (let i = flapPoints.length - 1; i >= 0; i--) {
            ctx.lineTo(transformX(flapPoints[i].x), transformY(flapPoints[i].yl));
        }
        
        ctx.closePath();
        
        // 플랩 스타일 (중간 톤의 회색)
        ctx.fillStyle = '#d0d0d0';
        ctx.strokeStyle = '#606060';
        ctx.lineWidth = 1;
        ctx.fill();
        ctx.stroke();
    }
    
    // 스포일러 렌더링
    function renderSpoilers() {
        if (spoilerPoints.length <= 0 || simulation.spoilerDeflection <= 0) return;
        
        // 패널별로 그룹화
        const spoilerPanels = {};
        
        for (let i = 0; i < spoilerPoints.length; i++) {
            const panelIndex = spoilerPoints[i].panelIndex;
            if (!spoilerPanels[panelIndex]) {
                spoilerPanels[panelIndex] = [];
            }
            spoilerPanels[panelIndex].push(spoilerPoints[i]);
        }
        
        // 각 패널 그리기
        for (let panel in spoilerPanels) {
            if (spoilerPanels[panel].length <= 1) continue;
            
            const points = spoilerPanels[panel].sort((a, b) => a.x - b.x);
            
            ctx.beginPath();
            
            // 스포일러 기저면 (날개 표면)
            ctx.moveTo(transformX(points[0].x), transformY(points[0].y));
            
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(transformX(points[i].x), transformY(points[i].y));
            }
            
            // 스포일러 상단 (끝에서부터)
            for (let i = points.length - 1; i >= 0; i--) {
                ctx.lineTo(
                    transformX(points[i].x), 
                    transformY(points[i].y + points[i].height)
                );
            }
            
            ctx.closePath();
            
            // 스포일러 스타일 (어두운 회색)
            ctx.fillStyle = '#b0b0b0';
            ctx.strokeStyle = '#404040';
            ctx.lineWidth = 1;
            ctx.fill();
            ctx.stroke();
        }
    }
    
    // 모든 날개 구성요소 렌더링
    function renderAirfoil() {
        ctx.save();
        
        // 기준점 (1/4 시위점)
        const referenceX = simulation.flowDirection === 'left-to-right'
            ? canvas.width * 0.25 + simulation.chord * 0.25
            : canvas.width * 0.75 - simulation.chord * 0.25;
        const referenceY = canvas.height / 2;
        
        // 구성요소 렌더링 (순서 중요: 뒤에서 앞으로)
        renderFlap();     // 플랩 (뒤)
        renderMainWing(); // 메인 날개 (중간)
        renderSpoilers(); // 스포일러 (상부 표면)
        renderSlat();     // 슬랫 (앞)
        
        ctx.restore();
    }
    
    // 정보 오버레이 표시 (한글 지원)
    function renderInfoOverlay() {
        const textX = 20;
        let textY = 30;
        const lineHeight = 20;
        
        // 배경 패널
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(10, 10, 230, 180);
        
        // 정보 텍스트
        ctx.font = '14px Arial';
        ctx.fillStyle = 'white';
        
        // 한글 텍스트 적용
        ctx.fillText('A320 날개 시스템 시뮬레이션', textX, textY);
        textY += lineHeight * 1.5;
        
        ctx.fillText(`받음각: ${simulation.angleOfAttack.toFixed(1)}°`, textX, textY);
        textY += lineHeight;
        
        // 플랩 설정 표시
        let flapText = "";
        switch(simulation.flapPosition) {
            case "UP": flapText = "0° (UP)"; break;
            case "1": flapText = "10° (CONF 1)"; break;
            case "2": flapText = "15° (CONF 2)"; break;
            case "3": flapText = "20° (CONF 3)"; break;
            case "FULL": flapText = `${simulation.flapDeflection}° (FULL)`; break;
        }
        
        ctx.fillText(`플랩 설정: ${flapText}`, textX, textY);
        textY += lineHeight;
        
        // 슬랫 설정 표시
        let slatText = "";
        switch(simulation.slatPosition) {
            case "UP": slatText = "0% (UP)"; break;
            case "MID": slatText = "18% (중간)"; break;
            case "1": slatText = "22% (CONF 1)"; break;
            case "2": slatText = "24% (CONF 2)"; break;
            case "3": slatText = "26% (CONF 3)"; break;
        }
        
        ctx.fillText(`슬랫 설정: ${slatText}`, textX, textY);
        textY += lineHeight;
        
        // 스포일러 설정 표시
        ctx.fillText(`스포일러: ${simulation.spoilerDeflection.toFixed(1)}°`, textX, textY);
        textY += lineHeight;
        
        ctx.fillText(`유동 속도: ${simulation.fluidVelocity.toFixed(1)} m/s`, textX, textY);
        textY += lineHeight * 1.5;
        
        // 압력 분포 범례
        const gradientWidth = 150;
        const gradientHeight = 15;
        const gradientX = textX;
        const gradientY = textY;
        
        // 그라데이션 생성
        const gradient = ctx.createLinearGradient(gradientX, 0, gradientX + gradientWidth, 0);
        gradient.addColorStop(0, 'blue');
        gradient.addColorStop(0.33, 'cyan');
        gradient.addColorStop(0.5, 'green');
        gradient.addColorStop(0.67, 'yellow');
        gradient.addColorStop(1, 'red');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(gradientX, gradientY, gradientWidth, gradientHeight);
        
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 1;
        ctx.strokeRect(gradientX, gradientY, gradientWidth, gradientHeight);
        
        ctx.fillStyle = 'white';
        ctx.fillText('저압', gradientX, gradientY + gradientHeight + 15);
        ctx.fillText('고압', gradientX + gradientWidth - 30, gradientY + gradientHeight + 15);
    }
    
    // 메인 렌더링 함수
    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 배경 (진한 녹색)
        ctx.fillStyle = '#004000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // 압력장, 유선, 날개 형상 렌더링
        renderPressureField();
        renderStreamlines();
        renderAirfoil();
        renderInfoOverlay();
    }
    
    // 시뮬레이션 업데이트 루프
    function updateSimulation() {
        updateParticles();
        render();
        
        if (simulation.running) {
            requestAnimationFrame(updateSimulation);
        }
    }
    
    // 시뮬레이션 초기화
    function initSimulation() {
        generateAirfoilShape();
        calculateFlow();
        initParticles();
        updateSimulation();
    }
    
    // UI 업데이트 함수들
    function updateFlapUI() {
        const flapValueText = document.getElementById('flapValue');
        const flapPositionText = document.getElementById('flapPosition');
        
        if (flapValueText) {
            flapValueText.textContent = simulation.flapDeflection.toFixed(1);
        }
        
        if (flapPositionText) {
            flapPositionText.textContent = simulation.flapPosition;
        }
    }
    
    function updateSlatUI() {
        const slatValueText = document.getElementById('slatValue');
        const slatPositionText = document.getElementById('slatPosition');
        
        if (slatValueText) {
            slatValueText.textContent = simulation.slatExtension.toFixed(1);
        }
        
        if (slatPositionText) {
            slatPositionText.textContent = simulation.slatPosition;
        }
    }
    
    function updateSpoilerUI() {
        const spoilerValueText = document.getElementById('spoilerValue');
        
        if (spoilerValueText) {
            spoilerValueText.textContent = simulation.spoilerDeflection.toFixed(1);
        }
    }
    
    // 컨트롤 설정
    function setupControls() {
        // 받음각 컨트롤
        const angleControl = document.getElementById('angleControl');
        const angleValue = document.getElementById('angleValue');
        
        if (angleControl && angleValue) {
            angleControl.value = simulation.angleOfAttack;
            angleValue.textContent = simulation.angleOfAttack.toFixed(1);
            
            angleControl.addEventListener('input', function(e) {
                simulation.angleOfAttack = parseFloat(e.target.value);
                angleValue.textContent = simulation.angleOfAttack.toFixed(1);
                calculateFlow();
            });
        }
        
        // A320 플랩 설정 컨트롤
        const flapControl = document.getElementById('flapControl');
        const flapValue = document.getElementById('flapValue');
        const flapPosition = document.getElementById('flapPosition');
        
        if (flapControl && flapValue && flapPosition) {
            flapControl.value = simulation.flapDeflection;
            flapValue.textContent = simulation.flapDeflection.toFixed(1);
            flapPosition.textContent = simulation.flapPosition;
            
            flapControl.addEventListener('input', function(e) {
                simulation.flapDeflection = parseFloat(e.target.value);
                
                // A320 플랩 설정에 따른 위치 결정
                if (simulation.flapDeflection <= 2) {
                    simulation.flapPosition = "UP";    // 수납
                } else if (simulation.flapDeflection <= 12) {
                    simulation.flapPosition = "1";     // 이륙1
                } else if (simulation.flapDeflection <= 17) {
                    simulation.flapPosition = "2";     // 이륙2
                } else if (simulation.flapDeflection <= 25) {
                    simulation.flapPosition = "3";     // 이륙3
                } else {
                    simulation.flapPosition = "FULL";  // 착륙
                }
                
                updateFlapUI();
                generateAirfoilShape();
                calculateFlow();
            });
        }
        
        // 플랩 설정 버튼들
        const flapButtons = document.querySelectorAll('.flap-setting-btn');
        
        if (flapButtons.length > 0) {
            flapButtons.forEach(btn => {
                btn.addEventListener('click', function() {
                    const setting = this.dataset.setting;
                    let angle = 0;
                    
                    // A320 플랩 설정 매핑
                    switch(setting) {
                        case "UP": angle = 0; break;
                        case "1": angle = 10; break;
                        case "2": angle = 15; break;
                        case "3": angle = 20; break;
                        case "FULL": angle = 35; break;
                        case "FULL_MAX": angle = 40; break;
                    }
                    
                    simulation.flapDeflection = angle;
                    simulation.flapPosition = setting === "FULL_MAX" ? "FULL" : setting;
                    
                    // UI 업데이트
                    if (flapControl) flapControl.value = angle;
                    updateFlapUI();
                    
                    // 시뮬레이션 업데이트
                    generateAirfoilShape();
                    calculateFlow();
                    
                    // 버튼 스타일 업데이트
                    flapButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }
        
        // A320 슬랫 설정 컨트롤
        const slatControl = document.getElementById('slatControl');
        const slatValue = document.getElementById('slatValue');
        const slatPosition = document.getElementById('slatPosition');
        
        if (slatControl && slatValue && slatPosition) {
            slatControl.value = simulation.slatExtension;
            slatValue.textContent = simulation.slatExtension.toFixed(1);
            slatPosition.textContent = simulation.slatPosition;
            
            slatControl.addEventListener('input', function(e) {
                simulation.slatExtension = parseFloat(e.target.value);
                
                // A320 슬랫 설정에 따른 위치 결정
                if (simulation.slatExtension <= 5) {
                    simulation.slatPosition = "UP";    // 수납
                } else if (simulation.slatExtension <= 20) {
                    simulation.slatPosition = "MID";   // 중간
                } else if (simulation.slatExtension <= 23) {
                    simulation.slatPosition = "1";     // 설정 1
                } else if (simulation.slatExtension <= 25) {
                    simulation.slatPosition = "2";     // 설정 2
                } else {
                    simulation.slatPosition = "3";     // 설정 3 (최대)
                }
                
                updateSlatUI();
                generateAirfoilShape();
                calculateFlow();
            });
        }
        
        // 슬랫 설정 버튼들
        const slatButtons = document.querySelectorAll('.slat-setting-btn');
        
        if (slatButtons.length > 0) {
            slatButtons.forEach(btn => {
                btn.addEventListener('click', function() {
                    const setting = this.dataset.slat;
                    let extension = 0;
                    
                    // A320 슬랫 설정 매핑
                    switch(setting) {
                        case "UP": extension = 0; break;
                        case "MID": extension = 18; break;
                        case "1": extension = 22; break;
                        case "2": extension = 24; break;
                        case "3": extension = 26; break;
                    }
                    
                    simulation.slatExtension = extension;
                    simulation.slatPosition = setting;
                    
                    // UI 업데이트
                    if (slatControl) slatControl.value = extension;
                    updateSlatUI();
                    
                    // 시뮬레이션 업데이트
                    generateAirfoilShape();
                    calculateFlow();
                    
                    // 버튼 스타일 업데이트
                    slatButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }
        
        // 스포일러 설정 컨트롤
        const spoilerControl = document.getElementById('spoilerControl');
        const spoilerValue = document.getElementById('spoilerValue');
        
        if (spoilerControl && spoilerValue) {
            spoilerControl.value = simulation.spoilerDeflection;
            spoilerValue.textContent = simulation.spoilerDeflection.toFixed(1);
            
            spoilerControl.addEventListener('input', function(e) {
                simulation.spoilerDeflection = parseFloat(e.target.value);
                
                updateSpoilerUI();
                generateAirfoilShape();
                calculateFlow();
            });
        }
        
        // 유동 속도 컨트롤
        const velocityControl = document.getElementById('velocityControl');
        const velocityValue = document.getElementById('velocityValue');
        
        if (velocityControl && velocityValue) {
            velocityControl.value = simulation.fluidVelocity;
            velocityValue.textContent = simulation.fluidVelocity.toFixed(1);
            
            velocityControl.addEventListener('input', function(e) {
                simulation.fluidVelocity = parseFloat(e.target.value);
                velocityValue.textContent = simulation.fluidVelocity.toFixed(1);
                calculateFlow();
            });
        }
        
        // 유동 방향 변경 컨트롤
        const directionControl = document.getElementById('directionControl');
        
        if (directionControl) {
            directionControl.value = simulation.flowDirection;
            
            directionControl.addEventListener('change', function(e) {
                simulation.flowDirection = e.target.value;
                generateAirfoilShape();
                calculateFlow();
                initParticles();
            });
        }
        
        // 시각화 옵션 토글
        const pressureToggle = document.getElementById('pressureToggle');
        const streamlineToggle = document.getElementById('streamlineToggle');
        
        if (pressureToggle) {
            pressureToggle.checked = simulation.showPressure;
            pressureToggle.addEventListener('change', function(e) {
                simulation.showPressure = e.target.checked;
            });
        }
        
        if (streamlineToggle) {
            streamlineToggle.checked = simulation.showStreamlines;
            streamlineToggle.addEventListener('change', function(e) {
                simulation.showStreamlines = e.target.checked;
            });
        }
        
        // 시뮬레이션 컨트롤 버튼
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
                // 기본값으로 재설정
                simulation.angleOfAttack = -5.0;
                simulation.flapDeflection = 20;
                simulation.flapPosition = "3";
                simulation.slatExtension = 25;
                simulation.slatPosition = "3";
                simulation.spoilerDeflection = 0;
                
                // UI 업데이트
                if (angleControl && angleValue) {
                    angleControl.value = simulation.angleOfAttack;
                    angleValue.textContent = simulation.angleOfAttack.toFixed(1);
                }
                
                if (flapControl) {
                    flapControl.value = simulation.flapDeflection;
                    updateFlapUI();
                }
                
                if (slatControl) {
                    slatControl.value = simulation.slatExtension;
                    updateSlatUI();
                }
                
                if (spoilerControl) {
                    spoilerControl.value = simulation.spoilerDeflection;
                    updateSpoilerUI();
                }
                
                // 버튼 상태 업데이트
                document.querySelector('.flap-setting-btn.active')?.classList.remove('active');
                document.querySelector('[data-setting="3"]')?.classList.add('active');
                
                document.querySelector('.slat-setting-btn.active')?.classList.remove('active');
                document.querySelector('[data-slat="3"]')?.classList.add('active');
                
                // 시뮬레이션 재초기화
                initSimulation();
            });
        }
    }
    
    // 초기화 및 시작
    setupControls();
    initSimulation();
});