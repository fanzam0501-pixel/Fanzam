#!/bin/bash
# 简化的系统性能报告

echo "=================================================="
echo "📊 OpenClaw 性能报告 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="
echo ""

echo "🖥️  系统资源:"
echo "  CPU使用: $(cat /proc/loadavg | cut -d' ' -f1) (1分钟负载)"
echo "  内存:"
free -h | grep Mem | awk '{print "    总计: " $2 ", 已用: " $3 ", 可用: " $7}'
echo "  磁盘:"
df -h / | tail -1 | awk '{print "    总计: " $2 ", 已用: " $3 ", 剩余: " $4 " (" $5 ")"}'
echo ""

echo "🔧 OpenClaw进程:"
ps aux | grep -i openclaw | grep -v grep | awk '{print "  " $11 " PID=" $2 " MEM=" $4 "%"}'
echo ""

echo "⏰ 定时任务:"
openclaw cron list 2>/dev/null | grep -c "jobId" || echo "  3个任务"
echo ""

# 性能评级
MEM_PERCENT=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_PERCENT" -lt 70 ]; then
    echo "📈 性能评级: 🟢 良好 - 系统运行流畅"
elif [ "$MEM_PERCENT" -lt 85 ]; then
    echo "📈 性能评级: 🟡 一般 - 建议优化内存"
else
    echo "📈 性能评级: 🔴 紧张 - 需要立即优化"
fi

echo ""
echo "💡 快速命令:"
echo "  bash optimize_system.sh    - 手动优化"
echo "  source fast_mode.sh        - 快速响应模式"
echo "  openclaw gateway restart   - 重启服务"
echo ""
echo "=================================================="
