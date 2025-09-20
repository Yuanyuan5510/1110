#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备检测工具
用于识别访问设备类型（手机/电脑）
"""

import re
from typing import Dict, Optional

class DeviceDetector:
    """设备检测器"""
    
    MOBILE_USER_AGENTS = [
        'android', 'iphone', 'ipad', 'ipod', 'windows phone',
        'mobile', 'blackberry', 'bb', 'opera mini', 'fennec',
        'kindle', 'silk', 'playbook', 'nexus', 'galaxy', 'palm'
    ]
    
    TABLET_USER_AGENTS = [
        'ipad', 'playbook', 'kindle', 'silk', 'tablet', 'nexus'
    ]
    
    @classmethod
    def detect_device(cls, user_agent: str) -> Dict[str, str]:
        """
        检测设备类型
        
        Args:
            user_agent: 用户代理字符串
            
        Returns:
            包含设备信息的字典
        """
        if not user_agent:
            return {
                'type': 'desktop',
                'name': 'Unknown Desktop',
                'is_mobile': False,
                'is_tablet': False,
                'is_desktop': True
            }
        
        user_agent_lower = user_agent.lower()
        
        # 检测是否为平板
        is_tablet = any(tablet in user_agent_lower for tablet in cls.TABLET_USER_AGENTS)
        
        # 检测是否为手机
        is_mobile = any(mobile in user_agent_lower for mobile in cls.MOBILE_USER_AGENTS)
        
        # 确定设备类型
        if is_tablet:
            device_type = 'tablet'
            is_mobile = False
        elif is_mobile:
            device_type = 'mobile'
        else:
            device_type = 'desktop'
        
        # 提取设备名称
        device_name = cls._extract_device_name(user_agent)
        
        return {
            'type': device_type,
            'name': device_name,
            'is_mobile': device_type == 'mobile',
            'is_tablet': device_type == 'tablet',
            'is_desktop': device_type == 'desktop',
            'user_agent': user_agent
        }
    
    @classmethod
    def _extract_device_name(cls, user_agent: str) -> str:
        """提取设备名称"""
        user_agent_lower = user_agent.lower()
        
        # 检测具体设备
        if 'iphone' in user_agent_lower:
            return 'iPhone'
        elif 'ipad' in user_agent_lower:
            return 'iPad'
        elif 'android' in user_agent_lower:
            # 提取Android设备信息
            android_match = re.search(r'android\s+([0-9.]+)', user_agent_lower)
            android_version = android_match.group(1) if android_match else ''
            
            # 尝试提取设备型号
            device_match = re.search(r';\s*([^;)]+)\s*build/', user_agent_lower)
            if device_match:
                device = device_match.group(1).strip()
                return f"Android {android_version} ({device})"
            else:
                return f"Android {android_version}"
        elif 'windows phone' in user_agent_lower:
            return 'Windows Phone'
        elif 'kindle' in user_agent_lower:
            return 'Kindle'
        else:
            # 检测浏览器
            if 'chrome' in user_agent_lower:
                return 'Chrome'
            elif 'firefox' in user_agent_lower:
                return 'Firefox'
            elif 'safari' in user_agent_lower:
                return 'Safari'
            elif 'edge' in user_agent_lower:
                return 'Edge'
            else:
                return 'Unknown'

# Flask集成
from flask import request

def get_device_info() -> Dict[str, str]:
    """从Flask请求中获取设备信息"""
    user_agent = request.headers.get('User-Agent', '')
    return DeviceDetector.detect_device(user_agent)