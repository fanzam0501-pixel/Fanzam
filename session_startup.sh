#!/bin/bash
# 会话启动优化脚本
# 在每次会话开始时自动运行

echo "🚀 会话启动优化..."

# 1. 刷新记忆缓存
cd /root/.openclaw/workspace
python3 -c "
from memory_cache import get_cache
cache = get_cache()
cache.refresh_if_needed()
print('✅ 记忆缓存已刷新')
" 2>/dev/null

# 2. 预加载关键数据
python3 -c "
from preload import preload_essentials
count = preload_essentials()
print(f'✅ {count} 个关键文件已预加载到内存')
" 2>/dev/null

# 3. 清理过期缓存
find /root/.openclaw/workspace -name "*.pyc" -delete 2>/dev/null
find /tmp -name "openclaw-*" -mtime +1 -delete 2>/dev/null

echo "⚡ 会话已就绪，响应速度已优化！"
