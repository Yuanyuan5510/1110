#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公开排行榜管理器
管理全局排行榜数据
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

class LeaderboardManager:
    """排行榜管理器"""
    
    def __init__(self, data_file: str = "leaderboard.json"):
        self.data_file = data_file
        self.scores = []
        self.load_scores()
    
    def load_scores(self):
        """加载排行榜数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.scores = json.load(f)
            except Exception:
                self.scores = []
        else:
            self.scores = []
    
    def save_scores(self):
        """保存排行榜数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存排行榜失败: {e}")
    
    def add_score(self, score: int, max_tile: int, moves: int, size: int, player_name: str = "匿名玩家"):
        """添加新分数到排行榜（兼容旧方法）"""
        self.add_or_update_score(player_name, score, max_tile, moves, size)
    
    def add_or_update_score(self, player_name: str, score: int, max_tile: int, moves: int, size: int):
        """更新或添加玩家分数（同一个玩家只保留最高分）"""
        # 查找是否已有该玩家的记录
        existing_entry = None
        for entry in self.scores:
            if entry['player_name'] == player_name:
                existing_entry = entry
                break
        
        new_entry = {
            'score': score,
            'max_tile': max_tile,
            'moves': moves,
            'size': size,
            'player_name': player_name,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        if existing_entry:
            # 如果新分数更高，则更新
            if score > existing_entry['score']:
                self.scores.remove(existing_entry)
                self.scores.append(new_entry)
        else:
            # 添加新玩家
            self.scores.append(new_entry)
        
        # 按分数排序，保留前100名
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:100]
        
        self.save_scores()
    
    def get_top_scores(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取排行榜前N名"""
        return self.scores[:limit]
    
    def get_rank_by_score(self, score: int) -> int:
        """根据分数获取排名"""
        for i, entry in enumerate(self.scores):
            if entry['score'] <= score:
                return i + 1
        return len(self.scores) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取排行榜统计信息"""
        if not self.scores:
            return {
                'total_players': 0,
                'highest_score': 0,
                'average_score': 0,
                'most_common_size': 4
            }
        
        total_players = len(self.scores)
        highest_score = max(s['score'] for s in self.scores)
        average_score = sum(s['score'] for s in self.scores) // total_players
        
        # 获取最常见的棋盘大小
        size_counts = {}
        for score in self.scores:
            size = score['size']
            size_counts[size] = size_counts.get(size, 0) + 1
        most_common_size = max(size_counts.items(), key=lambda x: x[1])[0]
        
        return {
            'total_players': total_players,
            'highest_score': highest_score,
            'average_score': average_score,
            'most_common_size': most_common_size
        }

# 全局排行榜实例
leaderboard = LeaderboardManager()