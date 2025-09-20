#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用工厂
创建和配置Flask应用
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import secrets
import json

from utils.config import GameConfig
from utils.device_detector import get_device_info
from game.game_logic import Game2048
from server.leaderboard import leaderboard

def create_app():
    """创建Flask应用"""
    from utils.config import GameConfig
    config = GameConfig()
    
    # 获取当前目录的绝对路径
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
    
    # 配置
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    app.config['CONFIG'] = config
    
    # 初始化SocketIO - 优化配置确保稳定运行
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)
    
    # 存储游戏状态
    games = {}  # session_id -> Game2048
    rooms = {}  # room_id -> {players: set(), game: Game2048}
    
    @app.route('/')
    def index():
        """主页路由"""
        device_info = get_device_info()
        
        # 检查是否为软件端请求
        if request.args.get('software') == 'true':
            template = 'software.html'
        elif device_info['is_mobile'] or device_info['is_tablet']:
            template = 'mobile.html'
        else:
            template = 'desktop.html'
        
        # 创建新的游戏实例
        session_id = session.get('session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['session_id'] = session_id
        
        if session_id not in games:
            games[session_id] = Game2048(4)
        
        return render_template(
            template,
            device_info=device_info,
            config=config.config
        )

    @app.route('/desktop')
    def desktop():
        return render_template('desktop.html', config=config.config)

    @app.route('/software')
    def software():
        return render_template('software_embedded.html', config=config.config)
    
    @app.route('/local')
    def local_access():
        """本地访问专用路由 - 确保打包后可直接访问"""
        return render_template('desktop.html', config=config.config)
    # 获取排行榜数据函数
    def get_leaderboard_data():
        """获取排行榜数据"""
        try:
            return leaderboard.get_top_scores()
        except Exception as e:
            return []

    @app.route('/api/leaderboard')
    def get_leaderboard():
        """获取排行榜"""
        try:
            data = get_leaderboard_data()
            response = jsonify(data)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/game/state')
    def get_game_state():
        """获取游戏状态"""
        try:
            session_id = session.get('session_id')
            if not session_id or session_id not in games:
                return jsonify({'error': 'Game not found'}), 404
            
            response = jsonify(games[session_id].get_state())
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/game/move', methods=['POST'])
    def make_move():
        """执行移动"""
        session_id = session.get('session_id')
        if not session_id or session_id not in games:
            return jsonify({'error': 'Game not found'}), 404
        
        data = request.get_json()
        direction = data.get('direction')
        
        game = games[session_id]
        moved = False
        
        if direction == 'left':
            moved = game.move_left()
        elif direction == 'right':
            moved = game.move_right()
        elif direction == 'up':
            moved = game.move_up()
        elif direction == 'down':
            moved = game.move_down()
        
        response = jsonify({
            'moved': moved,
            'state': game.get_state()
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @app.route('/api/game/new', methods=['POST'])
    def new_game():
        """开始新游戏"""
        session_id = session.get('session_id')
        if not session_id:
            session_id = secrets.token_hex(8)
            session['session_id'] = session_id
        
        data = request.get_json()
        size = data.get('size', 4)
        
        # 移动端限制最大8x8
        device_info = get_device_info()
        if (device_info['is_mobile'] or device_info['is_tablet']) and size > 8:
            size = 8
        
        games[session_id] = Game2048(size)
        
        response = jsonify(games[session_id].get_state())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @app.route('/api/game/scores')
    def get_scores():
        """获取公开排行榜"""
        try:
            scores = leaderboard.get_top_scores()
            response = jsonify(scores)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        except Exception as e:
            app.logger.error(f"获取排行榜失败: {e}")
            return jsonify({'error': str(e), 'scores': []}), 500

    @app.route('/api/game/scores', methods=['POST'])
    def add_score():
        """添加分数到排行榜（为每个玩家分配唯一ID并连续记录）"""
        try:
            data = request.get_json()
            score = data.get('score', 0)
            max_tile = data.get('max_tile', 0)
            moves = data.get('moves', 0)
            size = data.get('size', 4)
            
            # 获取或创建玩家ID
            player_id = session.get('player_id')
            if not player_id:
                player_id = str(secrets.token_hex(8))
                session['player_id'] = player_id
            
            # 使用玩家ID作为用户名，确保连续记录
            player_name = f"玩家_{player_id[:8]}"
            
            # 更新或添加分数（同一个玩家只保留最高分）
            leaderboard.add_or_update_score(player_name, score, max_tile, moves, size)
            
            response = jsonify({'success': True, 'player_id': player_id})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/game/leaderboard/stats')
    def get_leaderboard_stats():
        """获取排行榜统计信息"""
        response = jsonify(leaderboard.get_stats())
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @socketio.on('connect')
    def handle_connect():
        """处理连接"""
        print(f'Client connected: {request.sid}')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """处理断开连接"""
        print(f'Client disconnected: {request.sid}')
        
        # 清理游戏状态
        session_id = session.get('session_id')
        if session_id and session_id in games:
            del games[session_id]
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """加入房间"""
        room_id = data.get('room_id', 'default')
        
        if room_id not in rooms:
            rooms[room_id] = {
                'players': set(),
                'game': Game2048(4)
            }
        
        rooms[room_id]['players'].add(request.sid)
        join_room(room_id)
        
        emit('room_joined', {
            'room_id': room_id,
            'players_count': len(rooms[room_id]['players'])
        })
    
    @socketio.on('game_action')
    def handle_game_action(data):
        """处理游戏动作"""
        room_id = data.get('room_id', 'default')
        action = data.get('action')
        
        if room_id not in rooms:
            return
        
        game = rooms[room_id]['game']
        moved = False
        
        if action == 'move_left':
            moved = game.move_left()
        elif action == 'move_right':
            moved = game.move_right()
        elif action == 'move_up':
            moved = game.move_up()
        elif action == 'move_down':
            moved = game.move_down()
        elif action == 'new_game':
            size = data.get('size', 4)
            game = Game2048(size)
            rooms[room_id]['game'] = game
            moved = True
        
        if moved:
            # 广播游戏状态给房间内的所有玩家
            emit('game_state', game.get_state(), room=room_id)
    
    @app.route('/updates')
    def updates():
        return send_file('../updates.html')

    @app.route('/welcome')
    def welcome():
        return send_file('../welcome.html')

    @app.route('/updates.html')
    def updates_html():
        return send_file('../updates.html')

    @app.route('/welcome.html')
    def welcome_html():
        return send_file('../welcome.html')

    return app