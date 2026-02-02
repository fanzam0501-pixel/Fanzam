#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 响应速度优化配置生成器
"""

import json
import os

# 优化的Gateway配置
optimized_config = {
    "agents": {
        "defaults": {
            "model": {
                "primary": "kimi-code/kimi-for-coding"
            },
            "models": {
                "kimi-code/kimi-for-coding": {
                    "alias": "Kimi Code"
                }
            },
            "workspace": "/root/.openclaw/workspace",
            "maxConcurrent": 2,  # 降低并发，减少内存占用
            "subagents": {
                "maxConcurrent": 4  # 降低子代理并发
            },
            "streaming": {
                "enabled": True,  # 启用流式响应，更快感知
                "chunkSize": 100
            },
            "timeouts": {
                "tool": 30,  # 工具调用超时
                "llm": 60,   # LLM响应超时
                "total": 120 # 总超时
            }
        }
    },
    "gateway": {
        "port": 18789,
        "mode": "local",
        "bind": "loopback",
        "auth": {
            "mode": "token",
            "token": "auto"
        },
        "performance": {
            "enableKeepAlive": True,
            "keepAliveTimeout": 30000,
            "requestTimeout": 120000,
            "maxRequestsPerSocket": 100
        },
        "resources": {
            "maxMemoryMB": 512,  # 限制最大内存
            "gcInterval": 300    # 5分钟GC一次
        }
    },
    "channels": {
        "feishu": {
            "enabled": True,
            "performance": {
                "batchInterval": 100,  # 100ms批处理
                "maxRetries": 2        # 减少重试次数
            }
        }
    }
}

def apply_optimizations():
    config_path = "/root/.openclaw/openclaw.json"
    
    try:
        with open(config_path, 'r') as f:
            current = json.load(f)
        
        # 合并优化配置
        current['agents']['defaults'].update(optimized_config['agents']['defaults'])
        current['gateway'].update(optimized_config['gateway'])
        
        # 备份原配置
        backup_path = config_path + ".backup." + str(int(__import__('time').time()))
        os.rename(config_path, backup_path)
        
        # 写入优化配置
        with open(config_path, 'w') as f:
            json.dump(current, f, indent=2)
        
        print("✅ 配置优化完成!")
        print(f"📁 原配置备份: {backup_path}")
        print("\n优化内容:")
        print("  • 降低并发数 (4→2)")
        print("  • 启用流式响应")
        print("  • 限制内存 512MB")
        print("  • 缩短超时时间")
        print("\n重启后生效: openclaw gateway restart")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    apply_optimizations()
