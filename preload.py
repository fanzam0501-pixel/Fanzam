#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能预加载系统 - 会话开始时自动加载常用数据
"""

import json
import os

# 预加载的数据缓存
_PRELOADED = {}

def preload_essentials():
    """预加载关键数据到内存"""
    global _PRELOADED
    
    files_to_preload = {
        'memory': '/root/.openclaw/workspace/MEMORY.md',
        'identity': '/root/.openclaw/workspace/IDENTITY.md',
        'user': '/root/.openclaw/workspace/USER.md',
        'stock_config': '/root/.openclaw/workspace/stock_monitor_config.json',
    }
    
    for key, path in files_to_preload.items():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _PRELOADED[key] = f.read()
        except:
            _PRELOADED[key] = ''
    
    return len(_PRELOADED)

def get_preloaded(key):
    """获取预加载的数据"""
    return _PRELOADED.get(key, '')

def quick_user_info():
    """快速获取用户信息"""
    memory = get_preloaded('memory')
    
    # 快速解析关键信息
    info = {
        'name': '方逸灿',
        'timezone': 'Asia/Shanghai',
        'markets': ['A股', '港股']
    }
    
    # 从内存中快速扫描
    if '方逸灿' in memory:
        info['name'] = '方逸灿'
    if '东八区' in memory or 'Asia/Shanghai' in memory:
        info['timezone'] = 'Asia/Shanghai'
    
    return info

# 会话启动时自动预加载
if __name__ != '__main__':
    # 被导入时自动预加载
    preload_essentials()
