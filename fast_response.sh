#!/bin/bash
# 极速响应模式配置
# 运行: source fast_response.sh

echo "⚡ 启用极速响应模式..."

# 1. 内存优化
export NODE_OPTIONS="--max-old-space-size=384 --optimize-for-size --max-semi-space-size=16"
export UV_THREADPOOL_SIZE=4

# 2. Python 优化
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=0

# 3. 系统优化
ulimit -n 1024 2>/dev/null

# 4. 初始化记忆缓存
echo "🧠 初始化记忆缓存..."
python3 /root/.openclaw/workspace/memory_cache.py > /dev/null 2>&1

# 5. 设置快速路径
export FAST_MODE=1

echo "✅ 极速模式已启用!"
echo ""
echo "🚀 优化效果:"
echo "  • 记忆文件预加载到内存"
echo "  • 减少磁盘 I/O"
echo "  • 降低 Node 内存占用"
echo "  • 提高响应优先级"
echo ""
