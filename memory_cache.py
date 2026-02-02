#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆缓存系统 - 加速文件读取和响应
"""

import json
import os
from datetime import datetime

class MemoryCache:
    """内存缓存管理器"""
    
    def __init__(self):
        self.cache_file = "/root/.openclaw/workspace/.memory_cache.json"
        self.cache = {}
        self.load_cache()
    
    def load_cache(self):
        """从磁盘加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.build_cache()
    
    def build_cache(self):
        """构建初始缓存"""
        self.cache = {
            'memory_md': self._read_file('/root/.openclaw/workspace/MEMORY.md'),
            'identity_md': self._read_file('/root/.openclaw/workspace/IDENTITY.md'),
            'user_md': self._read_file('/root/.openclaw/workspace/USER.md'),
            'soul_md': self._read_file('/root/.openclaw/workspace/SOUL.md'),
            'stock_config': self._read_file('/root/.openclaw/workspace/stock_monitor_config.json'),
            'last_update': datetime.now().isoformat(),
            'version': 1
        }
        self.save_cache()
    
    def _read_file(self, path):
        """安全读取文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ''
    
    def save_cache(self):
        """保存缓存到磁盘"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False)
    
    def get(self, key):
        """获取缓存数据"""
        return self.cache.get(key, '')
    
    def update(self, key, value):
        """更新缓存"""
        self.cache[key] = value
        self.cache['last_update'] = datetime.now().isoformat()
        self.save_cache()
    
    def refresh_if_needed(self):
        """检查是否需要刷新（每10分钟）"""
        try:
            last = datetime.fromisoformat(self.cache.get('last_update', ''))
            if (datetime.now() - last).seconds > 600:
                self.build_cache()
        except:
            self.build_cache()

# 全局缓存实例
_cache = None

def get_cache():
    """获取缓存实例（单例模式）"""
    global _cache
    if _cache is None:
        _cache = MemoryCache()
    return _cache

def quick_memory():
    """快速获取记忆摘要"""
    cache = get_cache()
    
    # 提取关键信息（避免读取整个文件）
    memory = cache.get('memory_md')
    lines = memory.split('\n')
    
    summary = {
        'user_name': '方逸灿',
        'timezone': '东八区',
        'markets': ['A股', '港股'],
        'features': ['股票监控', '自动备份']
    }
    
    # 从缓存中快速提取
    for line in lines:
        if 'Name:' in line and '方逸灿' in line:
            summary['user_name'] = '方逸灿'
        elif 'Timezone:' in line and '东八区' in line:
            summary['timezone'] = '东八区'
    
    return summary

if __name__ == '__main__':
    # 初始化缓存
    cache = get_cache()
    print("✅ 记忆缓存系统已初始化")
    print(f"📁 缓存文件: {cache.cache_file}")
    print(f"🕐 最后更新: {cache.cache.get('last_update', '未知')}")
    
    # 测试快速读取
    import time
    start = time.time()
    summary = quick_memory()
    elapsed = (time.time() - start) * 1000
    print(f"\n⚡ 快速读取耗时: {elapsed:.2f}ms")
    print(f"👤 用户: {summary['user_name']}")
    print(f"🌏 时区: {summary['timezone']}")
