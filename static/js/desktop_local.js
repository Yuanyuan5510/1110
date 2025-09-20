// 本地电脑端JavaScript - 无需服务器
class Game2048 {
    constructor() {
        this.grid = [];
        this.score = 0;
        this.highScore = parseInt(localStorage.getItem('highScore')) || 0;
        this.moves = 0;
        this.size = 4;
        this.won = false;
        this.gameOver = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.newGame();
    }

    setupEventListeners() {
        document.getElementById('new-game-btn').addEventListener('click', () => this.newGame());
        document.getElementById('grid-size').addEventListener('change', (e) => {
            this.size = parseInt(e.target.value);
            this.newGame();
        });
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
    }

    newGame() {
        this.grid = Array(this.size).fill().map(() => Array(this.size).fill(0));
        this.score = 0;
        this.moves = 0;
        this.won = false;
        this.gameOver = false;
        this.addRandomTile();
        this.addRandomTile();
        this.updateDisplay();
        this.hideMessages();
    }

    addRandomTile() {
        const emptyCells = [];
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                if (this.grid[i][j] === 0) {
                    emptyCells.push({ x: i, y: j });
                }
            }
        }
        
        if (emptyCells.length > 0) {
            const { x, y } = emptyCells[Math.floor(Math.random() * emptyCells.length)];
            this.grid[x][y] = Math.random() < 0.9 ? 2 : 4;
        }
    }

    handleKeyPress(event) {
        if (this.gameOver) return;
        
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
        this.move(direction);
    }

    move(direction) {
        const rotated = this.rotateGrid(direction);
        const moved = this.moveLeft(rotated);
        
        if (moved.moved) {
            this.grid = this.rotateGridBack(moved.grid, direction);
            this.addRandomTile();
            this.moves++;
            this.updateDisplay();
            
            if (this.checkWin()) {
                this.won = true;
                this.showGameWon();
            } else if (this.checkGameOver()) {
                this.gameOver = true;
                this.showGameOver();
            }
        }
    }

    rotateGrid(direction) {
        let rotated = this.grid.map(row => [...row]);
        
        switch(direction) {
            case 'left':
                return rotated;
            case 'right':
                return rotated.map(row => row.reverse());
            case 'up':
                return this.transpose(rotated);
            case 'down':
                return this.transpose(rotated).map(row => row.reverse());
        }
    }

    rotateGridBack(grid, direction) {
        switch(direction) {
            case 'left':
                return grid;
            case 'right':
                return grid.map(row => row.reverse());
            case 'up':
                return this.transpose(grid);
            case 'down':
                return this.transpose(grid.map(row => row.reverse()));
        }
    }

    transpose(matrix) {
        return matrix[0].map((_, colIndex) => matrix.map(row => row[colIndex]));
    }

    moveLeft(grid) {
        let moved = false;
        const newGrid = [];
        
        for (let row of grid) {
            const filtered = row.filter(val => val !== 0);
            const merged = [];
            let scoreAdded = 0;
            
            for (let i = 0; i < filtered.length; i++) {
                if (i < filtered.length - 1 && filtered[i] === filtered[i + 1]) {
                    const mergedValue = filtered[i] * 2;
                    merged.push(mergedValue);
                    scoreAdded += mergedValue;
                    i++;
                    moved = true;
                } else {
                    merged.push(filtered[i]);
                }
            }
            
            while (merged.length < this.size) {
                merged.push(0);
            }
            
            for (let i = 0; i < this.size; i++) {
                if (row[i] !== merged[i]) {
                    moved = true;
                    break;
                }
            }
            
            newGrid.push(merged);
            this.score += scoreAdded;
        }
        
        return { grid: newGrid, moved: moved };
    }

    checkWin() {
        for (let row of this.grid) {
            if (row.includes(2048)) {
                return true;
            }
        }
        return false;
    }

    checkGameOver() {
        // 检查是否有空格
        for (let row of this.grid) {
            if (row.includes(0)) {
                return false;
            }
        }
        
        // 检查是否可以合并
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                const current = this.grid[i][j];
                if (
                    (i > 0 && this.grid[i-1][j] === current) ||
                    (i < this.size-1 && this.grid[i+1][j] === current) ||
                    (j > 0 && this.grid[i][j-1] === current) ||
                    (j < this.size-1 && this.grid[i][j+1] === current)
                ) {
                    return false;
                }
            }
        }
        
        return true;
    }

    updateDisplay() {
        this.renderGrid();
        document.getElementById('score').textContent = this.score;
        document.getElementById('high-score').textContent = this.highScore;
        document.getElementById('moves').textContent = this.moves;
        
        if (this.score > this.highScore) {
            this.highScore = this.score;
            localStorage.setItem('highScore', this.highScore);
        }
    }

    renderGrid() {
        const container = document.getElementById('grid-container');
        container.innerHTML = '';
        container.className = `grid-container grid-${this.size}`;
        container.style.gridTemplateColumns = `repeat(${this.size}, 1fr)`;
        
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                const value = this.grid[i][j];
                
                if (value !== 0) {
                    tile.textContent = value;
                    tile.classList.add(`tile-${value}`);
                }
                
                container.appendChild(tile);
            }
        }
    }

    showGameOver() {
        document.getElementById('final-score').textContent = this.score;
        document.getElementById('game-over').style.display = 'flex';
    }

    showGameWon() {
        document.getElementById('game-won').style.display = 'flex';
    }

    hideMessages() {
        document.getElementById('game-over').style.display = 'none';
        document.getElementById('game-won').style.display = 'none';
    }
}

// 继续游戏
function continueGame() {
    game.hideMessages();
}

// 新游戏
function newGame() {
    game.newGame();
}

// 初始化游戏
let game;
document.addEventListener('DOMContentLoaded', function() {
    game = new Game2048();
});