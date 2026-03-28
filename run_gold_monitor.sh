#!/bin/bash
# 金价监控执行脚本
# 根据运行模式发送报告到飞书

# 设置 PATH 确保能找到 openclaw 命令
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

cd /root/.openclaw/workspace

MODE=${1:-analysis}
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 运行监控脚本
OUTPUT=$(python3 gold_monitor.py "$MODE" 2>&1)

# 检查是否有提醒
if echo "$OUTPUT" | grep -q "\[HAS_ALERT\]"; then
    # 提取报告内容（去掉标记行）
    REPORT=$(echo "$OUTPUT" | grep -v "\[HAS_ALERT\]" | grep -v "\[NO_ALERT\]")

    # 发送飞书消息（使用绝对路径）
    /root/.nvm/versions/node/v22.22.0/bin/openclaw message send --message "$REPORT"

    echo "[$TIMESTAMP] 已发送金价提醒到飞书"
else
    echo "[$TIMESTAMP] 无转折点信号，跳过发送"
fi
