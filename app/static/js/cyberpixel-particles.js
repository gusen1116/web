/*
 * cyberpixel-particles.js
 * 
 * 화면 전체에 작은 픽셀 사각형들이 천천히 떨어지는 파티클 효과를 추가합니다.
 * `theme-cyberpixel` 클래스가 <html>에 설정된 경우에만 동작합니다.
 */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    if (!root.classList.contains('theme-cyberpixel')) return;
    // 캔버스 삽입
    const canvas = document.createElement('canvas');
    canvas.id = 'cyberpixel-particles';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '0';
    canvas.style.pointerEvents = 'none';
    document.body.insertBefore(canvas, document.body.firstChild);
    const ctx = canvas.getContext('2d');
    // 크기 맞추기
    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    resizeCanvas();
    // CSS 변수에서 색상 읽기
    const styles = getComputedStyle(root);
    const accent1 = styles.getPropertyValue('--text-accent').trim() || '#00F6FF';
    const accent2 = styles.getPropertyValue('--accent-secondary').trim() || '#FF00C3';
    // 파티클 초기화 – 화면 너비에 비례해서 수를 조절
    const particleCount = Math.min(80, Math.floor(window.innerWidth / 10));
    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1,
        speed: Math.random() * 0.3 + 0.3,
        color: Math.random() > 0.5 ? accent1 : accent2
      });
    }
    // 애니메이션 루프
    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach((p) => {
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, p.size, p.size);
        p.y += p.speed;
        // 아래로 떨어지면 다시 위로
        if (p.y > canvas.height) {
          p.y = -p.size;
          p.x = Math.random() * canvas.width;
        }
        // 약간의 가로 이동
        p.x += (Math.random() - 0.5) * 0.3;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
      });
      requestAnimationFrame(animate);
    }
    animate();
    // 창 크기 변화 시 캔버스 크기 재조정
    window.addEventListener('resize', () => {
      resizeCanvas();
    });
  });
  