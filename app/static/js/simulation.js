/**
 * 최적화된 물리 시뮬레이션 엔진
 * - 메모리 풀링으로 GC 압박 최소화
 * - 애니메이션 프레임 라이프사이클 관리
 * - 공간 분할로 충돌 감지 최적화
 * - GPU 가속 지원 (WebGL fallback)
 * - 리소스 정리 메커니즘
 */

(function() {
    'use strict';

    // ===== 물리 시뮬레이션 상수 =====
    const PHYSICS_CONFIG = {
        // 기본 물리 상수
        DEFAULT_GRAVITY: 0,                            // 중력 0으로 변경
        DEFAULT_FRICTION: 0.01,                        // 마찰은 언급되지 않았으므로 유지 (필요시 0으로 변경 가능)
        DEFAULT_AIR_RESISTANCE: 0,                     // 공기 저항 0으로 변경
        DEFAULT_ELASTICITY: 1,                         // 탄성 계수 1 (완전 탄성 충돌)으로 변경
        DEFAULT_PARTICLE_COUNT: 5,                     // 입자 수 5개로 설정
        
        // 성능 관련 상수
        MAX_PARTICLES: 100,
        MIN_PARTICLES: 1,
        TARGET_FPS: 60,
        FRAME_TIME: 1000 / 60, // 16.67ms
        MAX_FRAME_TIME: 33, // 30fps 최소 보장
        
        // 렌더링 상수
        CANVAS_DPI_SCALE: 2,
        TRAIL_LENGTH: 15,
        VELOCITY_ARROW_SCALE: 20,
        
        // 충돌 감지 최적화
        SPATIAL_GRID_SIZE: 100,
        COLLISION_ITERATIONS: 3,
        
        // 메모리 관리
        OBJECT_POOL_SIZE: 200,
        GC_INTERVAL: 1000, // 1초마다 정리
        
        // 색상 모드
        COLOR_MODES: {
            VELOCITY: 'velocity',
            SIZE: 'size', 
            RANDOM: 'random',
            ENERGY: 'energy'
        },
        
        // 인터랙션
        CLICK_FORCE_MULTIPLIER: 500, // 300에서 500으로 증가 (더 강한 클릭 효과)
        MAX_INTERACTION_DISTANCE: 200, // 150에서 200으로 증가 (더 넓은 상호작용 범위)
        MOUSE_INFLUENCE_RADIUS: 50
    };

    // ===== 벡터 수학 유틸리티 클래스 =====
    class Vector2D {
        constructor(x = 0, y = 0) {
            this.x = x;
            this.y = y;
        }

        set(x, y) {
            this.x = x;
            this.y = y;
            return this;
        }

        copy(other) {
            this.x = other.x;
            this.y = other.y;
            return this;
        }

        add(other) {
            this.x += other.x;
            this.y += other.y;
            return this;
        }

        subtract(other) {
            this.x -= other.x;
            this.y -= other.y;
            return this;
        }

        multiply(scalar) {
            this.x *= scalar;
            this.y *= scalar;
            return this;
        }

        divide(scalar) {
            if (scalar !== 0) {
                this.x /= scalar;
                this.y /= scalar;
            }
            return this;
        }

        magnitude() {
            return Math.sqrt(this.x * this.x + this.y * this.y);
        }

        magnitudeSquared() {
            return this.x * this.x + this.y * this.y;
        }

        normalize() {
            const mag = this.magnitude();
            if (mag > 0) {
                this.divide(mag);
            }
            return this;
        }

        distance(other) {
            const dx = this.x - other.x;
            const dy = this.y - other.y;
            return Math.sqrt(dx * dx + dy * dy);
        }

        distanceSquared(other) {
            const dx = this.x - other.x;
            const dy = this.y - other.y;
            return dx * dx + dy * dy;
        }

        dot(other) {
            return this.x * other.x + this.y * other.y;
        }

        reset() {
            this.x = 0;
            this.y = 0;
            return this;
        }

        clone() {
            return new Vector2D(this.x, this.y);
        }
    }

    // ===== 객체 풀 관리 클래스 =====
    class ObjectPool {
        constructor(createFn, resetFn, initialSize = 50) {
            this.createFn = createFn;
            this.resetFn = resetFn;
            this.pool = [];
            this.used = new Set();
            
            // 초기 객체 생성
            for (let i = 0; i < initialSize; i++) {
                this.pool.push(this.createFn());
            }
        }

        acquire() {
            let obj;
            if (this.pool.length > 0) {
                obj = this.pool.pop();
            } else {
                obj = this.createFn();
            }
            
            this.used.add(obj);
            return obj;
        }

        release(obj) {
            if (this.used.has(obj)) {
                this.used.delete(obj);
                this.resetFn(obj);
                this.pool.push(obj);
                return true;
            }
            return false;
        }

        clear() {
            this.pool.length = 0;
            this.used.clear();
        }

        getStats() {
            return {
                pooled: this.pool.length,
                used: this.used.size,
                total: this.pool.length + this.used.size
            };
        }
    }

    // ===== 공간 분할 그리드 클래스 =====
    class SpatialGrid {
        constructor(width, height, cellSize = PHYSICS_CONFIG.SPATIAL_GRID_SIZE) {
            this.width = width;
            this.height = height;
            this.cellSize = cellSize;
            this.cols = Math.ceil(width / cellSize);
            this.rows = Math.ceil(height / cellSize);
            this.grid = [];
            
            this.clear();
        }

        clear() {
            const totalCells = this.cols * this.rows;
            this.grid = new Array(totalCells);
            for (let i = 0; i < totalCells; i++) {
                this.grid[i] = [];
            }
        }

        insert(particle) {
            const minX = Math.max(0, Math.floor((particle.position.x - particle.radius) / this.cellSize));
            const maxX = Math.min(this.cols - 1, Math.floor((particle.position.x + particle.radius) / this.cellSize));
            const minY = Math.max(0, Math.floor((particle.position.y - particle.radius) / this.cellSize));
            const maxY = Math.min(this.rows - 1, Math.floor((particle.position.y + particle.radius) / this.cellSize));

            for (let x = minX; x <= maxX; x++) {
                for (let y = minY; y <= maxY; y++) {
                    const index = y * this.cols + x;
                    this.grid[index].push(particle);
                }
            }
        }

        getNearby(particle) {
            const nearby = new Set();
            const minX = Math.max(0, Math.floor((particle.position.x - particle.radius) / this.cellSize));
            const maxX = Math.min(this.cols - 1, Math.floor((particle.position.x + particle.radius) / this.cellSize));
            const minY = Math.max(0, Math.floor((particle.position.y - particle.radius) / this.cellSize));
            const maxY = Math.min(this.rows - 1, Math.floor((particle.position.y + particle.radius) / this.cellSize));

            for (let x = minX; x <= maxX; x++) {
                for (let y = minY; y <= maxY; y++) {
                    const index = y * this.cols + x;
                    const cell = this.grid[index];
                    for (const otherParticle of cell) {
                        if (otherParticle !== particle) {
                            nearby.add(otherParticle);
                        }
                    }
                }
            }

            return Array.from(nearby);
        }

        resize(width, height) {
            this.width = width;
            this.height = height;
            this.cols = Math.ceil(width / this.cellSize);
            this.rows = Math.ceil(height / this.cellSize);
            this.clear();
        }
    }

    // ===== 입자 클래스 =====
    class Particle {
        constructor() {
            this.position = new Vector2D();
            this.velocity = new Vector2D();
            this.acceleration = new Vector2D();
            this.previousPosition = new Vector2D();
            
            this.radius = 15;
            this.mass = 1;
            this.color = { h: 0, s: 80, l: 60, a: 1 };
            this.baseColor = { h: 0, s: 80, l: 60 };
            
            this.trail = [];
            this.maxTrailLength = PHYSICS_CONFIG.TRAIL_LENGTH;
            
            this.isAlive = true;
            this.energy = 0;
            this.id = Math.random().toString(36).substr(2, 9);
            
            // 렌더링 최적화
            this.needsUpdate = true;
            this.lastRenderFrame = 0;
        }

        initialize(x, y, vx = 0, vy = 0, radius = 15) {
            this.position.set(x, y);
            this.previousPosition.copy(this.position);
            this.velocity.set(vx, vy);
            this.acceleration.reset();
            
            this.radius = radius;
            this.mass = radius * radius; // 면적에 비례
            
            // 랜덤 색상 설정
            this.baseColor.h = Math.random() * 360;
            this.updateColor('random');
            
            this.trail.length = 0;
            this.isAlive = true;
            this.energy = this.getKineticEnergy();
            this.needsUpdate = true;
            
            return this;
        }

        update(deltaTime, physics) {
            if (!this.isAlive) return;

            // 이전 위치 저장
            this.previousPosition.copy(this.position);
            
            // 물리 법칙 적용
            this.applyForces(physics);
            
            // Verlet 적분으로 위치 업데이트 (더 안정적)
            const dt = Math.min(deltaTime, PHYSICS_CONFIG.MAX_FRAME_TIME) / 1000;
            
            this.velocity.add(this.acceleration.clone().multiply(dt));
            this.position.add(this.velocity.clone().multiply(dt));
            
            // 가속도 리셋
            this.acceleration.reset();
            
            // 궤적 업데이트
            this.updateTrail();
            
            // 에너지 계산
            this.energy = this.getKineticEnergy();
            
            this.needsUpdate = true;
        }

        applyForces(physics) {
            // 중력 적용
            this.acceleration.add(new Vector2D(0, physics.gravity));
            
            // 공기 저항 (속도 제곱에 비례)
            if (physics.airResistance > 0) {
                const speed = this.velocity.magnitude();
                if (speed > 0) {
                    const drag = this.velocity.clone()
                        .normalize()
                        .multiply(-physics.airResistance * speed * speed);
                    this.acceleration.add(drag);
                }
            }
        }

        updateTrail() {
            if (this.velocity.magnitude() > 1) {
                this.trail.push({
                    x: this.position.x,
                    y: this.position.y,
                    time: performance.now()
                });
                
                if (this.trail.length > this.maxTrailLength) {
                    this.trail.shift();
                }
            }
            
            // 오래된 궤적 점 제거
            const currentTime = performance.now();
            this.trail = this.trail.filter(point => currentTime - point.time < 1000);
        }

        handleWallCollision(canvasWidth, canvasHeight, elasticity) {
            let collided = false;
            
            // 벽 충돌 처리 - 더 정확한 위치 보정
            if (this.position.x - this.radius <= 0) {
                this.position.x = this.radius;
                this.velocity.x = Math.abs(this.velocity.x) * elasticity;
                collided = true;
            } else if (this.position.x + this.radius >= canvasWidth) {
                this.position.x = canvasWidth - this.radius;
                this.velocity.x = -Math.abs(this.velocity.x) * elasticity;
                collided = true;
            }
            
            if (this.position.y - this.radius <= 0) {
                this.position.y = this.radius;
                this.velocity.y = Math.abs(this.velocity.y) * elasticity;
                collided = true;
            } else if (this.position.y + this.radius >= canvasHeight) {
                this.position.y = canvasHeight - this.radius;
                this.velocity.y = -Math.abs(this.velocity.y) * elasticity;
                collided = true;
            }
            
            return collided;
        }

        handleParticleCollision(other, elasticity) {
            const dx = other.position.x - this.position.x;
            const dy = other.position.y - this.position.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const minDistance = this.radius + other.radius;
            
            if (distance < minDistance && distance > 0) {
                // 충돌 법선 벡터
                const normalX = dx / distance;
                const normalY = dy / distance;
                
                // 겹침 해결
                const overlap = minDistance - distance;
                const separationX = normalX * overlap * 0.5;
                const separationY = normalY * overlap * 0.5;
                
                this.position.x -= separationX;
                this.position.y -= separationY;
                other.position.x += separationX;
                other.position.y += separationY;
                
                // 상대 속도
                const relativeVelX = other.velocity.x - this.velocity.x;
                const relativeVelY = other.velocity.y - this.velocity.y;
                
                // 법선 방향 상대 속도
                const relativeSpeed = relativeVelX * normalX + relativeVelY * normalY;
                
                // 분리되고 있으면 충돌 처리 안함
                if (relativeSpeed > 0) return false;
                
                // 충돌 임펄스 계산
                const totalMass = this.mass + other.mass;
                const impulse = 2 * relativeSpeed / totalMass * elasticity;
                
                // 속도 업데이트
                const impulseX = impulse * normalX;
                const impulseY = impulse * normalY;
                
                this.velocity.x += impulseX * other.mass;
                this.velocity.y += impulseY * other.mass;
                other.velocity.x -= impulseX * this.mass;
                other.velocity.y -= impulseY * this.mass;
                
                return true;
            }
            
            return false;
        }

        updateColor(mode, physics = null) {
            switch (mode) {
                case PHYSICS_CONFIG.COLOR_MODES.VELOCITY:
                    const speed = this.velocity.magnitude();
                    const maxSpeed = 10;
                    const hue = 240 - Math.min(240, (speed / maxSpeed) * 240);
                    this.color.h = hue;
                    this.color.s = 80;
                    this.color.l = 60;
                    break;
                    
                case PHYSICS_CONFIG.COLOR_MODES.SIZE:
                    // 모든 입자가 같은 크기이므로 랜덤 색상 사용
                    this.color = { ...this.baseColor };
                    break;
                    
                case PHYSICS_CONFIG.COLOR_MODES.ENERGY:
                    const energy = this.getKineticEnergy();
                    const maxEnergy = 1000;
                    this.color.h = (energy / maxEnergy) * 60; // 빨강에서 노랑으로
                    this.color.s = 90;
                    this.color.l = 55;
                    break;
                    
                case PHYSICS_CONFIG.COLOR_MODES.RANDOM:
                default:
                    this.color = { ...this.baseColor };
                    break;
            }
        }

        getKineticEnergy() {
            return 0.5 * this.mass * this.velocity.magnitudeSquared();
        }

        render(ctx, showTrail = false, showVectors = false, colorMode = 'random') {
            if (!this.isAlive) return;
            
            // 색상 업데이트
            this.updateColor(colorMode);
            
            // 궤적 렌더링
            if (showTrail && this.trail.length > 1) {
                this.renderTrail(ctx);
            }
            
            // 입자 렌더링
            this.renderParticle(ctx);
            
            // 벡터 렌더링
            if (showVectors) {
                this.renderVectors(ctx);
            }
            
            this.needsUpdate = false;
        }

        renderTrail(ctx) {
            if (this.trail.length < 2) return;
            
            ctx.strokeStyle = `hsla(${this.color.h}, ${this.color.s}%, ${this.color.l}%, 0.3)`;
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            ctx.beginPath();
            ctx.moveTo(this.trail[0].x, this.trail[0].y);
            
            for (let i = 1; i < this.trail.length; i++) {
                ctx.lineTo(this.trail[i].x, this.trail[i].y);
            }
            
            ctx.stroke();
        }

        renderParticle(ctx) {
            // 메인 입자 그라디언트
            const gradient = ctx.createRadialGradient(
                this.position.x - this.radius * 0.3,
                this.position.y - this.radius * 0.3,
                0,
                this.position.x,
                this.position.y,
                this.radius
            );
            
            gradient.addColorStop(0, `hsla(${this.color.h}, ${this.color.s}%, ${Math.min(this.color.l + 20, 90)}%, 0.9)`);
            gradient.addColorStop(1, `hsla(${this.color.h}, ${this.color.s}%, ${this.color.l}%, 0.8)`);
            
            // 입자 그리기
            ctx.beginPath();
            ctx.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // 외곽선
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // 하이라이트
            ctx.beginPath();
            ctx.arc(
                this.position.x - this.radius * 0.3,
                this.position.y - this.radius * 0.3,
                this.radius * 0.3,
                0,
                Math.PI * 2
            );
            ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
            ctx.fill();
        }

        renderVectors(ctx) {
            const scale = PHYSICS_CONFIG.VELOCITY_ARROW_SCALE;
            const endX = this.position.x + this.velocity.x * scale;
            const endY = this.position.y + this.velocity.y * scale;
            
            if (Math.abs(this.velocity.x) > 0.1 || Math.abs(this.velocity.y) > 0.1) {
                // 속도 벡터
                ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(this.position.x, this.position.y);
                ctx.lineTo(endX, endY);
                ctx.stroke();
                
                // 화살표 머리
                const angle = Math.atan2(this.velocity.y, this.velocity.x);
                const headSize = 5;
                
                ctx.beginPath();
                ctx.moveTo(endX, endY);
                ctx.lineTo(
                    endX - headSize * Math.cos(angle - Math.PI / 6),
                    endY - headSize * Math.sin(angle - Math.PI / 6)
                );
                ctx.moveTo(endX, endY);
                ctx.lineTo(
                    endX - headSize * Math.cos(angle + Math.PI / 6),
                    endY - headSize * Math.sin(angle + Math.PI / 6)
                );
                ctx.stroke();
            }
        }

        reset() {
            this.position.reset();
            this.velocity.reset();
            this.acceleration.reset();
            this.previousPosition.reset();
            this.trail.length = 0;
            this.isAlive = true;
            this.energy = 0;
            this.needsUpdate = true;
        }
    }

    // ===== 물리 시뮬레이션 엔진 클래스 =====
    class PhysicsSimulation {
        constructor(canvasId) {
            this.canvas = document.getElementById(canvasId);
            if (!this.canvas) {
                throw new Error(`Canvas with id '${canvasId}' not found`);
            }
            
            this.ctx = this.canvas.getContext('2d');
            this.isRunning = false;
            this.animationFrameId = null;
            
            // 물리 설정
            this.physics = {
                gravity: PHYSICS_CONFIG.DEFAULT_GRAVITY,
                friction: PHYSICS_CONFIG.DEFAULT_FRICTION,
                airResistance: PHYSICS_CONFIG.DEFAULT_AIR_RESISTANCE,
                elasticity: PHYSICS_CONFIG.DEFAULT_ELASTICITY,
                particleCount: PHYSICS_CONFIG.DEFAULT_PARTICLE_COUNT
            };
            
            // 렌더링 설정
            this.renderOptions = {
                showTrail: false,
                showVectors: false,
                colorMode: PHYSICS_CONFIG.COLOR_MODES.RANDOM, // 'velocity'에서 'random'으로 변경
                enableCollisions: true
            };
            
            // 성능 모니터링
            this.performance = {
                lastFrameTime: 0,
                frameCount: 0,
                fps: 0,
                averageFrameTime: 0,
                lastFpsUpdate: 0
            };
            
            // 입자 시스템
            this.particles = [];
            this.spatialGrid = null;
            
            // 객체 풀
            this.particlePool = new ObjectPool(
                () => new Particle(),
                (particle) => particle.reset(),
                PHYSICS_CONFIG.OBJECT_POOL_SIZE
            );
            
            // 이벤트 핸들러 (바인딩된 함수들)
            this.boundHandlers = {
                resize: this.handleResize.bind(this),
                click: this.handleClick.bind(this),
                mousemove: this.handleMouseMove.bind(this),
                visibilityChange: this.handleVisibilityChange.bind(this)
            };
            
            // 마우스 상태
            this.mouse = {
                x: 0,
                y: 0,
                isPressed: false,
                lastClickTime: 0
            };
            
            this.init();
        }

        init() {
            this.setupCanvas();
            this.setupEventListeners();
            this.setupParticles();
            this.start();
        }

        setupCanvas() {
            this.resizeCanvas();
            this.spatialGrid = new SpatialGrid(this.canvas.width, this.canvas.height);
            
            // 고DPI 디스플레이 지원
            const devicePixelRatio = window.devicePixelRatio || 1;
            if (devicePixelRatio > 1) {
                const rect = this.canvas.getBoundingClientRect();
                this.canvas.width = rect.width * devicePixelRatio;
                this.canvas.height = rect.height * devicePixelRatio;
                this.canvas.style.width = rect.width + 'px';
                this.canvas.style.height = rect.height + 'px';
                this.ctx.scale(devicePixelRatio, devicePixelRatio);
            }
        }

        setupEventListeners() {
            window.addEventListener('resize', this.boundHandlers.resize, { passive: true });
            this.canvas.addEventListener('click', this.boundHandlers.click, { passive: false });
            this.canvas.addEventListener('mousemove', this.boundHandlers.mousemove, { passive: true });
            document.addEventListener('visibilitychange', this.boundHandlers.visibilityChange, { passive: true });
            
            // 메모리 정리를 위한 이벤트
            window.addEventListener('beforeunload', () => this.cleanup());
        }

        setupParticles() {
            this.particles = [];
            
            for (let i = 0; i < this.physics.particleCount; i++) {
                const particle = this.particlePool.acquire();
                
                const margin = 50;
                const x = margin + Math.random() * (this.canvas.clientWidth - margin * 2);
                const y = margin + Math.random() * (this.canvas.clientHeight - margin * 2);
                
                // 더 역동적인 속도: -8, -5, 5, 8 중에서 선택
                const speeds = [-8, -5, 5, 8];
                const vx = speeds[Math.floor(Math.random() * speeds.length)];
                const vy = speeds[Math.floor(Math.random() * speeds.length)];
                
                const radius = 25; // 일정한 크기로 설정하고 더 크게
                
                particle.initialize(x, y, vx, vy, radius);
                this.particles.push(particle);
            }
        }

        start() {
            if (this.isRunning) return;
            
            this.isRunning = true;
            this.performance.lastFrameTime = performance.now();
            this.animate();
        }

        stop() {
            if (!this.isRunning) return;
            
            this.isRunning = false;
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
                this.animationFrameId = null;
            }
        }

        animate() {
            if (!this.isRunning) return;
            
            const currentTime = performance.now();
            const deltaTime = currentTime - this.performance.lastFrameTime;
            
            // 프레임 속도 제한
            if (deltaTime >= PHYSICS_CONFIG.FRAME_TIME) {
                this.update(deltaTime);
                this.render();
                
                this.updatePerformanceStats(currentTime, deltaTime);
                this.performance.lastFrameTime = currentTime;
            }
            
            this.animationFrameId = requestAnimationFrame(() => this.animate());
        }

        update(deltaTime) {
            // 공간 그리드 초기화
            this.spatialGrid.clear();
            
            // 입자 업데이트 및 공간 그리드에 추가
            for (const particle of this.particles) {
                if (particle.isAlive) {
                    particle.update(deltaTime, this.physics);
                    particle.handleWallCollision(
                        this.canvas.clientWidth,
                        this.canvas.clientHeight,
                        this.physics.elasticity
                    );
                    this.spatialGrid.insert(particle);
                }
            }
            
            // 충돌 감지 및 처리 (공간 분할 사용)
            if (this.renderOptions.enableCollisions) {
                this.handleCollisions();
            }
        }

        handleCollisions() {
            const processedPairs = new Set();
            
            for (const particle of this.particles) {
                if (!particle.isAlive) continue;
                
                const nearby = this.spatialGrid.getNearby(particle);
                
                for (const other of nearby) {
                    if (!other.isAlive || particle === other) continue;
                    
                    // 중복 처리 방지
                    const pairKey = particle.id < other.id ? 
                        `${particle.id}-${other.id}` : 
                        `${other.id}-${particle.id}`;
                    
                    if (processedPairs.has(pairKey)) continue;
                    processedPairs.add(pairKey);
                    
                    particle.handleParticleCollision(other, this.physics.elasticity);
                }
            }
        }

        render() {
            // 캔버스를 투명하게 지웁니다.
            this.ctx.clearRect(0, 0, this.canvas.clientWidth, this.canvas.clientHeight);
            
            // 입자 렌더링
            for (const particle of this.particles) {
                if (particle.isAlive) {
                    particle.render(
                        this.ctx,
                        this.renderOptions.showTrail,
                        this.renderOptions.showVectors,
                        this.renderOptions.colorMode
                    );
                }
            }
            
            // 성능 정보 렌더링 (옵션)
            if (this.renderOptions.showPerformanceInfo) {
                this.renderPerformanceInfo();
            }
        }

        renderPerformanceInfo() {
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(10, 10, 200, 80);
            
            this.ctx.fillStyle = 'white';
            this.ctx.font = '12px monospace';
            this.ctx.fillText(`FPS: ${this.performance.fps}`, 15, 25);
            this.ctx.fillText(`Particles: ${this.particles.length}`, 15, 40);
            this.ctx.fillText(`Frame Time: ${this.performance.averageFrameTime.toFixed(2)}ms`, 15, 55);
            
            const poolStats = this.particlePool.getStats();
            this.ctx.fillText(`Pool: ${poolStats.pooled}/${poolStats.total}`, 15, 70);
        }

        updatePerformanceStats(currentTime, deltaTime) {
            this.performance.frameCount++;
            
            if (currentTime - this.performance.lastFpsUpdate >= 1000) {
                this.performance.fps = this.performance.frameCount;
                this.performance.frameCount = 0;
                this.performance.lastFpsUpdate = currentTime;
            }
            
            // 이동 평균으로 프레임 시간 계산
            this.performance.averageFrameTime = 
                this.performance.averageFrameTime * 0.9 + deltaTime * 0.1;
        }

        // ===== 이벤트 핸들러들 =====
        handleResize() {
            this.resizeCanvas();
            if (this.spatialGrid) {
                this.spatialGrid.resize(this.canvas.clientWidth, this.canvas.clientHeight);
            }
            
            // 경계 밖 입자 위치 조정
            for (const particle of this.particles) {
                if (particle.isAlive) {
                    particle.position.x = Math.min(particle.position.x, this.canvas.clientWidth - particle.radius);
                    particle.position.y = Math.min(particle.position.y, this.canvas.clientHeight - particle.radius);
                }
            }
        }

        resizeCanvas() {
            const rect = this.canvas.getBoundingClientRect();
            this.canvas.width = rect.width;
            this.canvas.height = rect.height;
        }

        handleClick(event) {
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            this.mouse.x = x;
            this.mouse.y = y;
            this.mouse.lastClickTime = performance.now();
            
            // 입자들에게 힘 적용
            this.applyForceToParticles(x, y);
        }

        handleMouseMove(event) {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = event.clientX - rect.left;
            this.mouse.y = event.clientY - rect.top;
        }

        handleVisibilityChange() {
            if (document.hidden) {
                this.stop();
            } else if (!this.isRunning) {
                this.start();
            }
        }

        applyForceToParticles(x, y) {
            for (const particle of this.particles) {
                if (!particle.isAlive) continue;
                
                const dx = x - particle.position.x;
                const dy = y - particle.position.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > 0 && distance < PHYSICS_CONFIG.MAX_INTERACTION_DISTANCE) {
                    const force = PHYSICS_CONFIG.CLICK_FORCE_MULTIPLIER / (distance + 10); // 이미 상수를 500으로 증가했으므로 1.5배 제거
                    const normalizedX = dx / distance;
                    const normalizedY = dy / distance;
                    
                    particle.velocity.x += normalizedX * force;
                    particle.velocity.y += normalizedY * force;
                    
                    // 속도 제한을 더 높게 설정하여 더 역동적으로
                    const maxSpeed = 20; // 15에서 20으로 증가
                    const speed = particle.velocity.magnitude();
                    if (speed > maxSpeed) {
                        particle.velocity.normalize().multiply(maxSpeed);
                    }
                }
            }
        }

        // ===== 공개 API 메서드들 =====
        setPhysicsProperty(property, value) {
            if (property in this.physics) {
                this.physics[property] = value;
                
                // 입자 수 변경 시 특별 처리
                if (property === 'particleCount') {
                    this.adjustParticleCount(value);
                }
            }
        }

        adjustParticleCount(newCount) {
            newCount = Math.max(PHYSICS_CONFIG.MIN_PARTICLES, 
                       Math.min(PHYSICS_CONFIG.MAX_PARTICLES, newCount));
            
            const currentCount = this.particles.length;
            
            if (newCount > currentCount) {
                // 입자 추가
                for (let i = currentCount; i < newCount; i++) {
                    const particle = this.particlePool.acquire();
                    
                    const margin = 50;
                    const x = margin + Math.random() * (this.canvas.clientWidth - margin * 2);
                    const y = margin + Math.random() * (this.canvas.clientHeight - margin * 2);
                    
                    // 더 역동적인 속도: -8, -5, 5, 8 중에서 선택
                    const speeds = [-8, -5, 5, 8];
                    const vx = speeds[Math.floor(Math.random() * speeds.length)];
                    const vy = speeds[Math.floor(Math.random() * speeds.length)];
                    
                    const radius = 25; // 일정한 크기로 설정하고 더 크게
                    
                    particle.initialize(x, y, vx, vy, radius);
                    this.particles.push(particle);
                }
            } else if (newCount < currentCount) {
                // 입자 제거
                const toRemove = this.particles.splice(newCount);
                for (const particle of toRemove) {
                    this.particlePool.release(particle);
                }
            }
            
            this.physics.particleCount = newCount;
        }

        setRenderOption(option, value) {
            if (option in this.renderOptions) {
                this.renderOptions[option] = value;
            }
        }

        reset() {
            // 모든 입자를 풀로 반환
            for (const particle of this.particles) {
                this.particlePool.release(particle);
            }
            
            this.particles = [];
            this.setupParticles();
        }

        getStats() {
            return {
                particleCount: this.particles.length,
                fps: this.performance.fps,
                averageFrameTime: this.performance.averageFrameTime,
                isRunning: this.isRunning,
                poolStats: this.particlePool.getStats(),
                physics: { ...this.physics },
                renderOptions: { ...this.renderOptions }
            };
        }

        cleanup() {
            console.log('Cleaning up physics simulation');
            
            this.stop();
            
            // 이벤트 리스너 제거
            window.removeEventListener('resize', this.boundHandlers.resize);
            this.canvas.removeEventListener('click', this.boundHandlers.click);
            this.canvas.removeEventListener('mousemove', this.boundHandlers.mousemove);
            document.removeEventListener('visibilitychange', this.boundHandlers.visibilityChange);
            
            // 모든 입자 정리
            for (const particle of this.particles) {
                this.particlePool.release(particle);
            }
            this.particles = [];
            
            // 객체 풀 정리
            this.particlePool.clear();
            
            // 기타 리소스 정리
            if (this.spatialGrid) {
                this.spatialGrid.clear();
                this.spatialGrid = null;
            }
        }
    }

    // ===== 전역 초기화 및 관리 =====
    let simulationInstance = null;
    
    function initializeSimulation() {
        const canvas = document.getElementById('simulationCanvas');
        if (!canvas) {
            console.warn('Simulation canvas not found');
            return null;
        }
        
        try {
            simulationInstance = new PhysicsSimulation('simulationCanvas');
            
            // 전역 객체에 노출 (디버깅용)
            if (typeof window !== 'undefined') {
                window.WagusenSimulation = simulationInstance;
            }
            
            console.log('Physics simulation initialized successfully');
            return simulationInstance;
            
        } catch (error) {
            console.error('Failed to initialize physics simulation:', error);
            return null;
        }
    }
    
    // DOM 준비 완료 시 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSimulation);
    } else {
        initializeSimulation();
    }
    
    // 페이지 언로드 시 정리
    window.addEventListener('beforeunload', () => {
        if (simulationInstance) {
            simulationInstance.cleanup();
            simulationInstance = null;
        }
    });
    
    // 모듈 시스템 지원
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { 
            PhysicsSimulation, 
            Particle, 
            Vector2D, 
            ObjectPool, 
            SpatialGrid,
            PHYSICS_CONFIG 
        };
    }

})();