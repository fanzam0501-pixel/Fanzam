#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存监控和自动优化守护进程
"""

import psutil
import os
import time
import sys

MEMORY_THRESHOLD = 80  # 内存使用超过80%时触发优化

def get_memory_usage():
    """获取内存使用率"""
    mem = psutil.virtual_memory()
    return mem.percent, mem.available / (1024 * 1024)  # MB

def optimize_memory():
    """执行内存优化"""
    print(f"[{time.strftime('%H:%M:%S')}] 🧠 内存紧张，执行优化...")
    
    # 清理Python缓存
    sys.modules.clear()
    
    # 触发系统GC
    import gc
    gc.collect()
    
    # 清理系统缓存
    os.system('sync && echo 1 > /proc/sys/vm/drop_caches 2>/dev/null')
    
    # 查找并清理大日志文件
    for root, dirs, files in os.walk('/root/.openclaw'):
        for file in files:
            if file.endswith('.log'):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                if size > 10:  # 大于10MB的日志
                    with open(filepath, 'w') as f:
                        f.write('')  # 清空
                    print(f"  清理日志: {filepath} ({size:.1f}MB)")

def monitor_loop():
    """监控循环"""
    print("🔍 内存监控启动 (阈值: 80%)")
    print("按 Ctrl+C 停止\n")
    
    while True:
        usage, available = get_memory_usage()
        print(f"[{time.strftime('%H:%M:%S')}] 内存: {usage}% | 可用: {available:.0f}MB", end='')
        
        if usage > MEMORY_THRESHOLD:
            print(" ⚠️")
            optimize_memory()
            # 优化后再次检查
            usage, available = get_memory_usage()
            print(f"  → 优化后: {usage}% | 可用: {available:.0f}MB")
        else:
            print(" ✓")
        
        time.sleep(30)  # 每30秒检查一次

if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n👋 监控停止")
