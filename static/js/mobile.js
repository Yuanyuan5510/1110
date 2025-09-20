// 移动端JavaScript - 修复版本
document.addEventListener('DOMContentLoaded', function() {
    let gameState = null;
    let gridSize = 4;
    let touchStartX = 0;
    let touchStartY = 0;
    let minSwipeDistance = 30;
    
    // DOM元素
    const gridContainer = document.getElementById('grid-container');
    const scoreElement = document.getElementById('score');
    const movesElement = document.getElementById('moves');
    const gridSizeSelect = document.getElementById('grid-size');
    const newGameBtn = document.getElementById('new-game-btn');
    const toggleControlsBtn = document.getElementById('toggle-controls');
    const virtualControls = document.getElementById('virtual-controls');
    const gameOverElement = document.getElementById('game-over');
    const gameWonElement = document.getElementById('game-won');
    const finalScoreElement = document.getElementById('final-score');
    const leaderboardList = document.getElementById('leaderboard-list');
    
    // 虚拟方向键
    const upBtn = document.getElementById('up-btn');
    const downBtn = document.getElementById('down-btn');
    const leftBtn = document.getElementById('left-btn');
    const rightBtn = document.getElementById('right-btn');
    
    // 初始化游戏
    initGame();
    
    // 事件监听器
    newGameBtn.addEventListener('click', newGame);
    gridSizeSelect.addEventListener('change', changeGridSize);
    toggleControlsBtn.addEventListener('click', toggleVirtualControls);
    
    // 触摸事件
    document.addEventListener('touchstart', handleTouchStart, { passive: false });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    // 虚拟方向键事件
    upBtn.addEventListener('click', () => makeMove('up'));
    downBtn.addEventListener('click', () => makeMove('down'));
    leftBtn.addEventListener('click', () => makeMove('left'));
    rightBtn.addEventListener('click', () => makeMove('right'));
    
    // 初始化游戏
    async function initGame() {
        try {
            const response = await fetch('/api/game/state');
            const data = await response.json();
            
            if (!data.error) {
                gameState = data;
                renderGrid();
                updateScore();
                loadLeaderboard();
            } else {
                await newGame();
            }
        } catch (error) {
            console.error('初始化游戏失败:', error);
            await newGame();
        }
    }
    
    // 创建新游戏
    async function newGame() {
        gridSize = parseInt(gridSizeSelect.value);
        
        try {
            const response = await fetch('/api/game/new', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ size: gridSize })
            });
            
            const data = await response.json();
            gameState = data;
            renderGrid();
            updateScore();
            hideMessages();
        } catch (error) {
            console.error('创建新游戏失败:', error);
        }
    }
    
    // 改变网格大小
    function changeGridSize() {
        newGame();
    }
    
    // 切换虚拟方向键显示
    function toggleVirtualControls() {
        const isVisible = virtualControls.style.display !== 'none';
        virtualControls.style.display = isVisible ? 'none' : 'flex';
        toggleControlsBtn.textContent = isVisible ? '显示按键' : '隐藏按键';
    }
    
    // 触摸事件处理
    function handleTouchStart(event) {
        if (gameState && gameState.game_over) return;
        
        const touch = event.touches[0];
        touchStartX = touch.clientX;
        touchStartY = touch.clientY;
    }
    
    function handleTouchMove(event) {
        event.preventDefault();
    }
    
    function handleTouchEnd(event) {
        if (event.changedTouches.length === 1) {
            const touchEndX = event.changedTouches[0].clientX;
            const touchEndY = event.changedTouches[0].clientY;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            if (Math.abs(deltaX) > minSwipeDistance || Math.abs(deltaY) > minSwipeDistance) {
                if (Math.abs(deltaX) > Math.abs(deltaY)) {
                    makeMove(deltaX > 0 ? 'right' : 'left');
                } else {
                    makeMove(deltaY > 0 ? 'down' : 'up');
                }
            }
        }
    }
    
    // 执行移动
    async function makeMove(direction) {
        if (!gameState || gameState.game_over) return;
        
        try {
            const response = await fetch('/api/game/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction })
            });
            
            const data = await response.json();
            
            if (data.moved) {
                gameState = data.state;
                renderGrid();
                updateScore();
                
                if (gameState.won) {
                    showGameWon();
                } else if (gameState.game_over) {
                    showGameOver();
                    await recordScore();
                }
            }
        } catch (error) {
            console.error('移动失败:', error);
        }
    }
    
    // 记录分数
    async function recordScore() {
        if (!gameState || gameState.score === 0) return;
        
        try {
            // 获取或生成设备ID
            let deviceId = localStorage.getItem('device_id');
            if (!deviceId) {
                deviceId = 'mobile_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('device_id', deviceId);
            }
            
            await fetch('/api/game/scores', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    score: gameState.score,
                    max_tile: gameState.max_tile,
                    moves: gameState.moves,
                    size: gameState.size,
                    device_id: deviceId,
                    player_name: '手机玩家'
                })
            });
            
            await loadLeaderboard();
        } catch (error) {
            console.error('记录分数失败:', error);
        }
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
        movesElement.textContent = gameState.moves;
    }
    
    // 加载排行榜
    async function loadLeaderboard() {
        try {
            const response = await fetch('/api/game/scores');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('Content-Type');
            if (!contentType || contentType.indexOf('application/json') === -1) {
                throw new Error('非JSON响应');
            }
            
            const scores = await response.json();
            
            if (!Array.isArray(scores)) {
                throw new Error('排行榜数据格式错误');
            }
            
            leaderboardList.innerHTML = '';
            const validScores = scores.filter(score => score && score.score > 0);
            validScores.slice(0, 5).forEach((score, index) => {
                const item = document.createElement('div');
                item.className = 'leaderboard-item';
                item.innerHTML = `
                    <span>${index + 1}. ${score.player_name || '匿名玩家'}</span>
                    <span>${score.score}分</span>
                `;
                leaderboardList.appendChild(item);
            });
            
            if (validScores.length === 0) {
                leaderboardList.innerHTML = '<div class="leaderboard-item">暂无数据</div>';
            }
        } catch (error) {
            console.error('加载排行榜失败:', error);
            leaderboardList.innerHTML = '<div class="leaderboard-item">加载失败</div>';
        }
    }
    
    // 显示游戏结束
    function showGameOver() {
        finalScoreElement.textContent = gameState.score;
        gameOverElement.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    // 显示游戏胜利
    function showGameWon() {
        gameWonElement.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    // 隐藏消息
    function hideMessages() {
        gameOverElement.style.display = 'none';
        gameWonElement.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    // 全局函数
    window.newGame = newGame;
    window.continueGame = hideMessages;
    
    // 设置定时器，每2秒更新一次排行榜（更快更新）
    setInterval(loadLeaderboard, 1000);
    
    // 页面可见性变化时更新
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            loadLeaderboard();
        }
    });
    
    // 窗口获得焦点时更新
    window.addEventListener('focus', loadLeaderboard);
    
    // 页面加载完成后立即更新
    window.addEventListener('load', loadLeaderboard);
    
    // 网络连接恢复时更新
    window.addEventListener('online', loadLeaderboard);
    
    // 防止页面缩放
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // 防止双击缩放
    document.addEventListener('dblclick', function(e) {
        e.preventDefault();
    });
});