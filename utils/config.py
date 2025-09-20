#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏配置文件
"""

import os
import json
from typing import Dict, Any

class GameConfig:
    """游戏配置类"""
    
    def __init__(self):
        self.config_file = "game_config.json"
        self.default_config = {
            "game": {
                "min_size": 4,
                "max_size": 10,
                "mobile_max_size": 8,
                "target_score": 2048
            },
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "ui": {
                "window_width": 800,
                "window_height": 600,
                "cell_size": 60,
                "margin": 10
            },
            "theme": {
                "background": "#faf8ef",
                "empty_cell": "#cdc1b4",
                "grid_color": "#bbada0",
                "text_color": "#776e65",
                "tile_colors": {
                    2: "#eee4da",
                    4: "#ede0c8",
                    8: "#f2b179",
                    16: "#f59563",
                    32: "#f67c5f",
                    64: "#f65e3b",
                    128: "#edcf72",
                    256: "#edcc61",
                    512: "#edc850",
                    1024: "#edc53f",
                    2048: "#edc22e"
                }
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置
                merged_config = self.default_config.copy()
                self._deep_update(merged_config, config)
                return merged_config
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                return self.default_config.copy()
        else:
            # 创建默认配置文件
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> None:
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> None:
        """深度更新字典"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default=None):
        """获取配置值，支持点分路径"""
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value) -> None:
        """设置配置值，支持点分路径"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()