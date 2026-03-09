#!/bin/bash
# 自动 Git 提交脚本
# 由 cron 定时调用，自动备份工作区到 GitHub

REPO_DIR="/root/.openclaw/workspace"
cd "$REPO_DIR"

# 标记文件路径
MANUAL_BACKUP_FILE="$REPO_DIR/.manual_backup_requested"
LAST_BACKUP_TIME_FILE="$REPO_DIR/.last_backup_time"
FORCE_BACKUP_FILE="$REPO_DIR/.force_backup_due_to_topics"

# 在检查备份条件前，先运行话题检测器（检测新话题并可能创建强制备份文件）
echo "$(date '+%Y-%m-%d %H:%M:%S') - 运行话题检测器..."
python3 "$REPO_DIR/topic_detector.py" check

# 初始化备份原因变量
BACKUP_REASON=""

# 手动备份提醒：如果存在标记文件，则强制备份
if [ -f "$MANUAL_BACKUP_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 检测到手动备份请求，执行备份"
    BACKUP_REASON="manual"
    rm -f "$MANUAL_BACKUP_FILE"
    # 继续执行备份
elif [ -f "$FORCE_BACKUP_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 检测到话题数量达到阈值，执行备份"
    BACKUP_REASON="topic_threshold"
    rm -f "$FORCE_BACKUP_FILE"
    # 继续执行备份
else
    # 检查是否有新的沟通内容（通过 memory/ 目录的修改时间判断）
    # 获取 memory/ 目录下最新文件的修改时间
    latest_memory_time=0
    if [ -d "$REPO_DIR/memory" ]; then
        latest_memory_time=$(find "$REPO_DIR/memory" -type f -name "*.md" -exec stat -c %Y {} \; | sort -n | tail -1)
    fi
    # 获取上次备份时间
    last_backup_time=0
    if [ -f "$LAST_BACKUP_TIME_FILE" ]; then
        last_backup_time=$(cat "$LAST_BACKUP_TIME_FILE")
    fi
    # 如果 memory/ 没有新文件，且没有 Git 变更，则跳过备份
    if [ "$latest_memory_time" -le "$last_backup_time" ]; then
        # 检查 Git 是否有变更
        if git diff --quiet && git diff --cached --quiet; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - 无新的沟通内容且无 Git 变更，跳过备份"
            exit 0
        fi
    fi
fi

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 无变更，跳过提交"
    exit 0
fi

# 添加所有变更
git add -A

# 提交，使用时间戳作为提交信息
COMMIT_MSG="auto: $(date '+%Y-%m-%d %H:%M:%S') 自动备份

变更文件:
$(git status --short)

由小爪自动提交"

git commit -m "$COMMIT_MSG" || exit 0

# 推送到远程（如果有）
if git remote get-url origin >/dev/null 2>&1; then
    git push origin master 2>&1
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 已推送到 GitHub: https://github.com/fanzam0501-pixel/Fanzam"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 已本地提交，但未配置远程仓库"
fi

# 记录本次备份时间
date +%s > "$LAST_BACKUP_TIME_FILE"

# 根据备份原因记录日志
if [ "$BACKUP_REASON" = "manual" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 手动备份完成"
elif [ "$BACKUP_REASON" = "topic_threshold" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 话题阈值触发备份完成"
    # 显示重置后状态
    python3 "$REPO_DIR/topic_detector.py" status
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 常规备份完成"
fi
