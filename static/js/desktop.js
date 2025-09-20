// 电脑端JavaScript
document.addEventListener('DOMContentLoaded', function() {
    let gameState = null;
    let gridSize = 4;
    
    // DOM元素
    const gridContainer = document.getElementById('grid-container');
    const scoreElement = document.getElementById('score');
    const highScoreElement = document.getElementById('high-score');
    const movesElement = document.getElementById('moves');
    const gridSizeSelect = document.getElementById('grid-size');
    const newGameBtn = document.getElementById('new-game-btn');
    const gameOverElement = document.getElementById('game-over');
    const gameWonElement = document.getElementById('game-won');
    const finalScoreElement = document.getElementById('final-score');
    const leaderboardList = document.getElementById('leaderboard-list');
    
    // 初始化游戏
    initGame();
    
    // 事件监听器
    newGameBtn.addEventListener('click', newGame);
    gridSizeSelect.addEventListener('change', changeGridSize);
    document.addEventListener('keydown', handleKeyPress);
    
    // 初始化游戏
    function initGame() {
        // 从本地存储加载上次分数
        try {
            const lastScore = localStorage.getItem('lastScore');
            const lastHighScore = localStorage.getItem('lastHighScore');
            const lastMoves = localStorage.getItem('lastMoves');
            
            if (lastScore) scoreElement.textContent = lastScore;
            if (lastHighScore) highScoreElement.textContent = lastHighScore;
            if (lastMoves) movesElement.textContent = lastMoves;
        } catch (e) {
            console.warn('无法从本地存储加载分数:', e);
        }
        
        fetch('/api/game/state')
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    gameState = data;
                    renderGrid();
                    updateScore();
                    loadLeaderboard();
                } else {
                    newGame();
                }
            })
            .catch(console.error);
    }
    
    // 创建新游戏
    function newGame() {
        gridSize = parseInt(gridSizeSelect.value);
        
        fetch('/api/game/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ size: gridSize })
        })
        .then(response => response.json())
        .then(data => {
            gameState = data;
            renderGrid();
            updateScore();
            hideMessages();
        })
        .catch(console.error);
    }
    
    // 改变网格大小
    function changeGridSize() {
        newGame();
    }
    
    // 处理键盘事件
    function handleKeyPress(event) {
        if (gameState && gameState.game_over) return;
        
        let direction = null;
        switch(event.key) {
            case 'ArrowLeft':
                direction = 'left';
                break;
            case 'ArrowRight':
                direction = 'right';
                break;
            case 'ArrowUp':
                direction = 'up';
                break;
            case 'ArrowDown':
                direction = 'down';
                break;
            default:
                return;
        }
        
        event.preventDefault();
        makeMove(direction);
    }
    
    // 执行移动
    function makeMove(direction) {
        fetch('/api/game/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ direction: direction })
        })
        .then(response => response.json())
        .then(data => {
            if (data.moved) {
                gameState = data.state;
                renderGrid();
                updateScore();
                
                // 实时记录分数到排行榜
                if (gameState.score > 0) {
                    recordScore(gameState.score, gameState.max_tile, gameState.moves, gameState.size);
                }
                
                if (gameState.won) {
                    showGameWon();
                } else if (gameState.game_over) {
                    showGameOver();
                    // 游戏结束时记录最终分数
                    recordScore(gameState.score, gameState.size);
                }
            }
        })
        .catch(console.error);
    }
    
    // 记录分数到排行榜
function recordScore(score, max_tile, moves, size) {
    fetch('/api/game/scores', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ score: score, max_tile: max_tile, moves: moves, size: size })
    })
        .then(response => response.json())
        .then(() => {
            loadLeaderboard();
        })
        .catch(console.error);
}
    
    // 渲染网格
    function renderGrid() {
        if (!gameState) return;
        
        const size = gameState.size;
        gridContainer.innerHTML = '';
        gridContainer.className = `grid-container grid-${size}`;
        gridContainer.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
        
        for (let i = 0; i < size; i++) {
            for (let j = 0; j < size; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                const value = gameState.grid[i][j];
                
                if (value !== 0) {
                    tile.textContent = value;
                    tile.classList.add(`tile-${value}`);
                }
                
                gridContainer.appendChild(tile);
            }
        }
    }
    
    // 更新分数
    function updateScore() {
        if (!gameState) return;
        
        scoreElement.textContent = gameState.score;
        highScoreElement.textContent = gameState.high_score;
        movesElement.textContent = gameState.moves;
        
        // 实时保存分数到本地存储
        try {
            localStorage.setItem('lastScore', gameState.score);
            localStorage.setItem('lastHighScore', gameState.high_score);
            localStorage.setItem('lastMoves', gameState.moves);
        } catch (e) {
            console.warn('无法保存分数到本地存储:', e);
        }
    }
    
    // 加载排行榜
    function loadLeaderboard() {
        fetch('/api/game/scores')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const contentType = response.headers.get('Content-Type');
                if (!contentType || contentType.indexOf('application/json') === -1) {
                    throw new Error('非JSON响应');
                }
                return response.json();
            })
            .then(scores => {
                if (!Array.isArray(scores)) {
                    throw new Error('排行榜数据格式错误');
                }
                leaderboardList.innerHTML = '';
                scores.forEach((score, index) => {
                    const item = document.createElement('div');
                    item.className = 'leaderboard-item';
                    item.innerHTML = `
                        <span>${index + 1}. ${score.player_name || '匿名玩家'}</span>
                        <span>${score.score}分</span>
                    `;
                    leaderboardList.appendChild(item);
                });
            })
            .catch(error => {
                console.error('加载排行榜失败:', error);
                leaderboardList.innerHTML = '<div class="leaderboard-item">加载失败</div>';
            });
    }
    
    // 显示游戏结束
    function showGameOver() {
        finalScoreElement.textContent = gameState.score;
        gameOverElement.style.display = 'flex';
        
        // 添加点击任意位置开启新游戏
        gameOverElement.addEventListener('click', function onClick() {
            gameOverElement.removeEventListener('click', onClick);
            newGame();
        });
    }
    
    // 显示游戏胜利
    function showGameWon() {
        gameWonElement.style.display = 'flex';
    }
    
    // 隐藏消息
    function hideMessages() {
        gameOverElement.style.display = 'none';
        gameWonElement.style.display = 'none';
    }
    
    // 全局函数供HTML调用
    window.newGame = newGame;
    window.continueGame = function() {
        hideMessages();
    };
    
    // 定期更新排行榜
    setInterval(loadLeaderboard, 30000);
});