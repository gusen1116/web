document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('tetris');
    const context = canvas.getContext('2d');
    const nextCanvas = document.getElementById('next');
    const nextContext = nextCanvas.getContext('2d');
    const scoreElement = document.getElementById('score');
    const startButton = document.getElementById('start');

    context.scale(20, 20);
    nextContext.scale(20, 20);

    const ARENA_WIDTH = 12;
    const ARENA_HEIGHT = 20;

    let arena = createMatrix(ARENA_WIDTH, ARENA_HEIGHT);

    const player = {
        pos: { x: 0, y: 0 },
        matrix: null,
        score: 0,
        next: null,
    };

    let dropCounter = 0;
    let dropInterval = 1000;
    let lastTime = 0;
    let isPaused = true;

    const colors = [
        null, '#FF0D72', '#0DC2FF', '#0DFF72', '#F538FF', '#FF8E0D', '#FFE138', '#3877FF'
    ];

    function createPiece(type) {
        if (type === 'T') return [[0, 0, 0], [1, 1, 1], [0, 1, 0]];
        if (type === 'O') return [[2, 2], [2, 2]];
        if (type === 'L') return [[0, 3, 0], [0, 3, 0], [0, 3, 3]];
        if (type === 'J') return [[0, 4, 0], [0, 4, 0], [4, 4, 0]];
        if (type === 'I') return [[0, 5, 0, 0], [0, 5, 0, 0], [0, 5, 0, 0], [0, 5, 0, 0]];
        if (type === 'S') return [[0, 6, 6], [6, 6, 0], [0, 0, 0]];
        if (type === 'Z') return [[7, 7, 0], [0, 7, 7], [0, 0, 0]];
    }

    function drawMatrix(matrix, offset) {
        matrix.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value !== 0) {
                    context.fillStyle = colors[value];
                    context.fillRect(x + offset.x, y + offset.y, 1, 1);
                }
            });
        });
    }

    function drawNextPiece() {
        nextContext.fillStyle = '#000';
        nextContext.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
        if (player.next) {
            const piece = player.next;
            const xOffset = (nextCanvas.width / 20 - piece[0].length) / 2;
            const yOffset = (nextCanvas.height / 20 - piece.length) / 2;
            
            piece.forEach((row, y) => {
                row.forEach((value, x) => {
                    if (value !== 0) {
                        nextContext.fillStyle = colors[value];
                        nextContext.fillRect(x + xOffset, y + yOffset, 1, 1);
                    }
                });
            });
        }
    }
    
    function draw() {
        context.fillStyle = '#000';
        context.fillRect(0, 0, canvas.width, canvas.height);
        drawMatrix(arena, { x: 0, y: 0 });
        drawMatrix(player.matrix, player.pos);
        drawNextPiece();
    }

    function createMatrix(width, height) {
        const matrix = [];
        while (height--) {
            matrix.push(new Array(width).fill(0));
        }
        return matrix;
    }

    function collide(arena, player) {
        const [m, o] = [player.matrix, player.pos];
        for (let y = 0; y < m.length; ++y) {
            for (let x = 0; x < m[y].length; ++x) {
                if (m[y][x] !== 0 && (arena[y + o.y] && arena[y + o.y][x + o.x]) !== 0) {
                    return true;
                }
            }
        }
        return false;
    }

    function merge(arena, player) {
        player.matrix.forEach((row, y) => {
            row.forEach((value, x) => {
                if (value !== 0) {
                    arena[y + player.pos.y][x + player.pos.x] = value;
                }
            });
        });
    }

    function playerDrop() {
        player.pos.y++;
        if (collide(arena, player)) {
            player.pos.y--;
            merge(arena, player);
            playerReset();
            arenaSweep();
            updateScore();
        }
        dropCounter = 0;
    }

    function playerMove(dir) {
        player.pos.x += dir;
        if (collide(arena, player)) {
            player.pos.x -= dir;
        }
    }

    function playerReset() {
        const pieces = 'ILJOTSZ';
        player.matrix = player.next || createPiece(pieces[pieces.length * Math.random() | 0]);
        player.next = createPiece(pieces[pieces.length * Math.random() | 0]);
        player.pos.y = 0;
        player.pos.x = (arena[0].length / 2 | 0) - (player.matrix[0].length / 2 | 0);

        if (collide(arena, player)) {
            gameOver();
        }
    }

    function playerRotate(dir) {
        const pos = player.pos.x;
        let offset = 1;
        rotate(player.matrix, dir);
        while (collide(arena, player)) {
            player.pos.x += offset;
            offset = -(offset + (offset > 0 ? 1 : -1));
            if (offset > player.matrix[0].length) {
                rotate(player.matrix, -dir);
                player.pos.x = pos;
                return;
            }
        }
    }

    function rotate(matrix, dir) {
        for (let y = 0; y < matrix.length; ++y) {
            for (let x = 0; x < y; ++x) {
                [matrix[x][y], matrix[y][x]] = [matrix[y][x], matrix[x][y]];
            }
        }
        if (dir > 0) {
            matrix.forEach(row => row.reverse());
        } else {
            matrix.reverse();
        }
    }

    function arenaSweep() {
        let rowCount = 1;
        outer: for (let y = arena.length - 1; y > 0; --y) {
            for (let x = 0; x < arena[y].length; ++x) {
                if (arena[y][x] === 0) {
                    continue outer;
                }
            }
            const row = arena.splice(y, 1)[0].fill(0);
            arena.unshift(row);
            ++y;
            player.score += rowCount * 10;
            rowCount *= 2;
        }
    }

    function updateScore() {
        scoreElement.innerText = player.score;
    }
    
    function update(time = 0) {
        if (isPaused) return;

        const deltaTime = time - lastTime;
        lastTime = time;

        dropCounter += deltaTime;
        if (dropCounter > dropInterval) {
            playerDrop();
        }

        draw();
        requestAnimationFrame(update);
    }
    
    function gameOver() {
        isPaused = true;
        alert(`게임 오버! 최종 점수: ${player.score}`);
        const playerName = prompt("리더보드에 등록할 이름을 입력하세요:", "GUSEN");
        if (playerName) {
            saveScore(playerName, player.score);
        }
    }

    async function saveScore(name, score) {
        try {
            await fetch('/api/score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player: name, score: score }),
            });
        } catch (error) {
            console.error('점수 저장 실패:', error);
        }
    }

    function startGame() {
        isPaused = false;
        arena = createMatrix(ARENA_WIDTH, ARENA_HEIGHT);
        player.score = 0;
        updateScore();
        playerReset();
        update();
    }

    document.addEventListener('keydown', event => {
        if (isPaused) return;
        if (event.key === 'ArrowLeft') playerMove(-1);
        else if (event.key === 'ArrowRight') playerMove(1);
        else if (event.key === 'ArrowDown') playerDrop();
        else if (event.key === 'q' || event.key === 'Q') playerRotate(-1);
        else if (event.key === 'w' || event.key === 'W') playerRotate(1);
    });
    
    startButton.addEventListener('click', () => {
        if(isPaused) {
            startGame();
            startButton.textContent = "재시작";
        } else {
            isPaused = true; // 게임 일시정지 개념은 없으므로 재시작으로 처리
            startGame();
        }
    });

    playerReset();
    updateScore();
    draw(); // 초기 화면 그리기
});