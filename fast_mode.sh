#!/bin/bash
# 快速响应模式 - 临时提升性能
# 使用方法: source fast_mode.sh

echo "⚡ 启用快速响应模式..."

# 1. 设置环境变量优化响应
export NODE_OPTIONS="--max-old-space-size=512 --optimize-for-size"
export PYTHONDONTWRITEBYTECODE=1  # 不生成.pyc文件
export PYTHONUNBUFFERED=1  # 无缓冲输出

# 2. 清理当前会话缓存
alias clear-cache='sync && echo 1 > /proc/sys/vm/drop_caches 2>/dev/null && echo "✅ 缓存已清理"'

# 3. 快速Git提交
alias quick-git='cd /root/.openclaw/workspace && git add -A && git commit -m "auto: $(date +%H:%M:%S)" && git push'

# 4. 内存查看
alias mem='free -h | grep Mem && echo "" && ps aux --sort=-%mem | head -5'

# 5. 快速股票检查
alias stock='cd /root/.openclaw/workspace && python3 stock_analyzer.py 盘前 2>/dev/null | head -30'

echo "✅ 快速模式已启用!"
echo ""
echo "快捷命令:"
echo "  clear-cache  - 清理系统缓存"
echo "  quick-git    - 快速提交Git"
echo "  mem          - 查看内存使用"
echo "  stock        - 快速股票分析"
echo ""
echo "提示: 这些别名只在当前会话有效"
