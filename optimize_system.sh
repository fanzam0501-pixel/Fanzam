#!/bin/bash
# OpenClaw 系统性能优化脚本
# 运行方式: bash optimize_openclaw.sh

echo "🚀 OpenClaw 性能优化开始..."

# 1. 清理系统缓存
echo "📦 清理系统缓存..."
sync
echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || true

# 2. 清理旧日志
echo "📝 清理旧日志文件..."
find /root/.openclaw -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
find /root/.openclaw -name "*.log.old" -type f -delete 2>/dev/null || true

# 3. 清理临时文件
echo "🗑️ 清理临时文件..."
rm -rf /tmp/openclaw-* 2>/dev/null || true
rm -rf /root/.openclaw/tmp/* 2>/dev/null || true

# 4. 压缩旧报告
echo "📊 压缩旧股票报告..."
find /root/.openclaw/workspace/stock_reports -name "*.txt" -type f -mtime +30 -exec gzip {} \; 2>/dev/null || true

# 5. 限制Node内存使用
echo "🧠 设置Node内存限制..."
export NODE_OPTIONS="--max-old-space-size=512"

# 6. 优化Git仓库
echo "🔧 优化Git仓库..."
cd /root/.openclaw/workspace
git gc --auto 2>/dev/null || true

echo "✅ 优化完成!"
free -h | grep Mem
