#!/bin/bash
# 话题检测脚本 - 由cron定期调用

REPO_DIR="/root/.openclaw/workspace"
cd "$REPO_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 运行话题检测器 (cron)"
python3 "$REPO_DIR/topic_detector.py" check

# 如果有强制备份文件，记录但不执行备份（备份由主脚本处理）
if [ -f "$REPO_DIR/.force_backup_due_to_topics" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 检测到话题阈值已达到，等待下次备份执行"
fi