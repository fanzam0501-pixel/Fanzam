#!/bin/bash
# 自动 Git 提交脚本
# 由 cron 定时调用，自动备份工作区到 GitHub

REPO_DIR="/root/.openclaw/workspace"
cd "$REPO_DIR"

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
