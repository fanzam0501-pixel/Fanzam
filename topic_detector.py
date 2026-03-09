#!/usr/bin/env python3
"""
话题检测脚本 V2
根据用户要求：一组连续对话中，某个话题关键词出现超过15次即为大的话题
一组连续对话只产出一个话题，达到10个不同话题后自动触发备份
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
import time

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
TOPIC_TRACKER_FILE = os.path.join(REPO_DIR, ".topic_tracker_v2.json")
FORCE_BACKUP_FILE = os.path.join(REPO_DIR, ".force_backup_due_to_topics")
MEMORY_DIR = os.path.join(REPO_DIR, "memory")

# 话题关键词定义（保持原有分类，但检测逻辑改为频率统计）
TOPIC_KEYWORDS = {
    "股票": ["股票", "股市", "投资", "交易", "上证", "深证", "港股", "A股", "基金", "证券", "涨停", "跌停", "行情", "涨跌", "大盘", "指数", "股价"],
    "AI": ["AI", "人工智能", "模型", "算法", "机器学习", "深度学习", "神经网络", "GPT", "Claude", "大语言模型", "LLM", "生成式AI", "智能助手"],
    "文本创作": ["文本", "创作", "写作", "文章", "小说", "文案", "编辑", "修改", "润色", "校对", "翻译", "文档", "内容", "段落"],
    "编程": ["编程", "代码", "开发", "软件", "程序", "算法", "数据结构", "Python", "JavaScript", "Java", "C++", "Git", "API", "调试", "部署"],
    "系统管理": ["系统", "管理", "运维", "服务器", "网络", "安全", "配置", "部署", "监控", "日志", "备份", "恢复", "性能", "优化"],
    "项目管理": ["项目", "管理", "计划", "任务", "进度", "团队", "协作", "沟通", "会议", "文档", "里程碑", "交付", "风险", "资源"],
    "学习": ["学习", "教育", "培训", "课程", "教材", "考试", "研究", "学术", "论文", "知识", "读书", "复习", "练习", "测试"],
    "生活": ["生活", "日常", "健康", "饮食", "运动", "娱乐", "旅行", "购物", "家庭", "朋友", "休息", "假期", "兴趣", "爱好"],
    "工作": ["工作", "职业", "职场", "同事", "领导", "面试", "简历", "招聘", "薪资", "绩效", "晋升", "离职", "加班", "会议"],
    "技术": ["技术", "科技", "创新", "产品", "设计", "硬件", "软件", "互联网", "移动", "应用", "开发", "测试", "发布", "更新"],
}

# 反向映射：关键词 -> 话题类别（用于快速查找）
KEYWORD_TO_TOPIC = {}
for topic, keywords in TOPIC_KEYWORDS.items():
    for keyword in keywords:
        KEYWORD_TO_TOPIC[keyword.lower()] = topic

def load_topic_tracker() -> Dict:
    """加载话题追踪器数据"""
    # 首先检查是否存在旧的V1数据文件
    old_tracker_file = os.path.join(REPO_DIR, ".topic_tracker.json")
    new_tracker_file = TOPIC_TRACKER_FILE
    
    # 如果新文件不存在但旧文件存在，迁移数据
    if not os.path.exists(new_tracker_file) and os.path.exists(old_tracker_file):
        print("检测到旧版话题追踪器，正在迁移数据...")
        try:
            with open(old_tracker_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            # 迁移数据
            migrated_data = migrate_v1_to_v2(old_data)
            
            # 保存新格式
            with open(new_tracker_file, 'w', encoding='utf-8') as f:
                json.dump(migrated_data, f, ensure_ascii=False, indent=2)
            
            print(f"数据迁移完成: {len(migrated_data['detected_topics'])} 个话题已导入")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"迁移失败: {e}")
    
    # 加载新格式数据
    if os.path.exists(new_tracker_file):
        try:
            with open(new_tracker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 确保版本正确
            if data.get("version", 1) < 2:
                data = migrate_v1_to_v2(data)
                save_topic_tracker(data)
                
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载追踪器失败: {e}")
    
    # 默认数据结构 V2
    return {
        "version": 2,
        "detected_topics": [],           # 已检测到的话题列表
        "current_conversation": {
            "start_time": 0,             # 当前对话组开始时间
            "keyword_counts": {},        # 关键词计数 {关键词: 次数}
            "topic_counts": {},          # 话题类别计数 {话题: 次数}
            "last_message_time": 0       # 最后一条消息时间
        },
        "threshold": 15,                 # 话题触发阈值（15次）
        "backup_threshold": 10,          # 备份触发阈值（10个话题）
        "last_reset_time": 0,
        "conversation_timeout": 1800,    # 对话组超时时间（秒）：30分钟
        "last_checked_time": 0
    }

def migrate_v1_to_v2(old_data: Dict) -> Dict:
    """将V1格式数据迁移到V2格式"""
    # 提取已检测到的话题
    detected_topics = []
    if "all_detected_topics" in old_data:
        detected_topics = old_data["all_detected_topics"]
    elif "current_session_topics" in old_data:
        detected_topics = old_data["current_session_topics"]
    
    # 确保话题列表唯一
    detected_topics = list(set(detected_topics))
    
    return {
        "version": 2,
        "detected_topics": detected_topics,
        "current_conversation": {
            "start_time": old_data.get("last_checked_time", 0),
            "keyword_counts": {},
            "topic_counts": {},
            "last_message_time": old_data.get("last_checked_time", 0)
        },
        "threshold": 15,
        "backup_threshold": 10,
        "last_reset_time": old_data.get("last_reset_time", 0),
        "conversation_timeout": 1800,
        "last_checked_time": old_data.get("last_checked_time", 0)
    }

def save_topic_tracker(data: Dict):
    """保存话题追踪器数据"""
    with open(TOPIC_TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词（属于预定义话题的）"""
    keywords_found = []
    text_lower = text.lower()
    
    # 检查每个关键词是否在文本中
    for keyword, topic in KEYWORD_TO_TOPIC.items():
        if keyword in text_lower:
            keywords_found.append(keyword)
    
    return keywords_found

def update_conversation_state(tracker: Dict, text: str, message_time: int) -> Tuple[bool, str]:
    """
    更新对话状态并检查是否检测到新话题
    返回: (是否检测到话题, 检测到的话题)
    """
    current = tracker["current_conversation"]
    threshold = tracker["threshold"]
    
    # 检查对话组是否超时（30分钟无消息）
    if current["last_message_time"] > 0:
        time_since_last = message_time - current["last_message_time"]
        if time_since_last > tracker["conversation_timeout"]:
            # 对话组超时，重置当前对话
            print(f"对话组超时（{time_since_last}秒），重置")
            current["start_time"] = message_time
            current["keyword_counts"] = {}
            current["topic_counts"] = {}
    
    # 如果是新对话组，设置开始时间
    if current["start_time"] == 0:
        current["start_time"] = message_time
    
    # 更新最后消息时间
    current["last_message_time"] = message_time
    
    # 提取关键词并更新计数
    keywords = extract_keywords(text)
    for keyword in keywords:
        # 更新关键词计数
        current["keyword_counts"][keyword] = current["keyword_counts"].get(keyword, 0) + 1
        
        # 获取该关键词所属的话题类别
        topic = KEYWORD_TO_TOPIC.get(keyword)
        if topic:
            # 更新话题类别计数
            current["topic_counts"][topic] = current["topic_counts"].get(topic, 0) + 1
    
    # 检查是否有话题达到阈值
    detected_topic = None
    for topic, count in current["topic_counts"].items():
        if count >= threshold:
            detected_topic = topic
            break
    
    if detected_topic:
        # 记录话题
        if detected_topic not in tracker["detected_topics"]:
            tracker["detected_topics"].append(detected_topic)
        
        # 重置当前对话组（开始新的对话组）
        current["start_time"] = message_time
        current["keyword_counts"] = {}
        current["topic_counts"] = {}
        current["last_message_time"] = message_time
        
        # 检查是否达到备份阈值
        if len(tracker["detected_topics"]) >= tracker["backup_threshold"]:
            print(f"检测到第{len(tracker['detected_topics'])}个话题，达到备份阈值{tracker['backup_threshold']}")
            # 创建触发备份的文件
            with open(FORCE_BACKUP_FILE, 'w') as f:
                f.write(f"话题数量达到阈值 {len(tracker['detected_topics'])}，触发备份")
            
            # 重置检测到的话题列表（开始新一轮计数）
            tracker["detected_topics"] = []
            tracker["last_reset_time"] = message_time
        
        return True, detected_topic
    
    return False, ""

def analyze_latest_memory():
    """分析最新的记忆文件，更新话题状态"""
    latest_file = get_latest_memory_file()
    if not latest_file:
        print("未找到记忆文件")
        return
    
    # 获取文件修改时间作为消息时间
    try:
        file_mtime = os.path.getmtime(latest_file)
    except OSError:
        file_mtime = int(time.time())
    
    # 读取文件内容
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except (IOError, UnicodeDecodeError) as e:
        print(f"读取记忆文件失败: {e}")
        return
    
    # 只分析最近的内容（最后2000字符）
    recent_content = content[-2000:]
    if not recent_content.strip():
        print("记忆文件内容为空")
        return
    
    # 加载追踪器
    tracker = load_topic_tracker()
    
    # 检查是否已经分析过该文件
    last_checked = tracker.get("last_checked_time", 0)
    if file_mtime <= last_checked:
        print(f"文件已分析过（最后检查: {datetime.fromtimestamp(last_checked)})")
        return
    
    # 更新对话状态
    detected, topic = update_conversation_state(tracker, recent_content, int(file_mtime))
    
    if detected:
        print(f"{datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')} - 检测到新话题: {topic}")
        print(f"已检测话题数: {len(tracker['detected_topics'])}/{tracker['backup_threshold']}")
    
    # 更新最后检查时间
    tracker["last_checked_time"] = int(time.time())
    
    # 保存追踪器
    save_topic_tracker(tracker)

def get_latest_memory_file() -> str:
    """获取最新的记忆文件"""
    if not os.path.exists(MEMORY_DIR):
        return ""
    
    md_files = []
    for file in os.listdir(MEMORY_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(MEMORY_DIR, file)
            try:
                md_files.append((file_path, os.path.getmtime(file_path)))
            except OSError:
                continue
    
    if not md_files:
        return ""
    
    # 按修改时间排序，获取最新的文件
    md_files.sort(key=lambda x: x[1], reverse=True)
    return md_files[0][0]

def show_topic_status():
    """显示话题状态"""
    tracker = load_topic_tracker()
    
    print(f"=== 话题检测状态 V2 ===")
    print(f"检测阈值: {tracker['threshold']}次/话题")
    print(f"备份阈值: {tracker['backup_threshold']}个话题")
    print(f"已检测话题数: {len(tracker['detected_topics'])}/{tracker['backup_threshold']}")
    print(f"已检测话题: {', '.join(tracker['detected_topics']) if tracker['detected_topics'] else '无'}")
    
    current = tracker["current_conversation"]
    if current["last_message_time"] > 0:
        print(f"\n当前对话组:")
        print(f"  开始时间: {datetime.fromtimestamp(current['start_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  最后消息: {datetime.fromtimestamp(current['last_message_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  话题计数:")
        for topic, count in sorted(current["topic_counts"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {topic}: {count}/{tracker['threshold']}")
        
        if current["keyword_counts"]:
            print(f"  关键词计数 (TOP 5):")
            for keyword, count in sorted(current["keyword_counts"].items(), key=lambda x: x[1], reverse=True)[:5]:
                topic = KEYWORD_TO_TOPIC.get(keyword, "未知")
                print(f"    {keyword} ({topic}): {count}")
    
    print(f"\n最后重置时间: {datetime.fromtimestamp(tracker['last_reset_time']).strftime('%Y-%m-%d %H:%M:%S') if tracker['last_reset_time'] else '从未'}")
    print(f"最后检查时间: {datetime.fromtimestamp(tracker['last_checked_time']).strftime('%Y-%m-%d %H:%M:%S') if tracker['last_checked_time'] else '从未'}")

def reset_topic_counter():
    """重置话题计数器"""
    tracker = load_topic_tracker()
    tracker["detected_topics"] = []
    tracker["current_conversation"] = {
        "start_time": 0,
        "keyword_counts": {},
        "topic_counts": {},
        "last_message_time": 0
    }
    tracker["last_reset_time"] = int(time.time())
    save_topic_tracker(tracker)
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 话题计数器已重置")

def test_keyword_extraction():
    """测试关键词提取"""
    test_texts = [
        "今天的股票行情怎么样？我觉得股市可能会涨。",
        "AI技术发展很快，机器学习算法越来越先进。",
        "我需要写一篇文章，关于文本创作和编辑技巧。"
    ]
    
    for text in test_texts:
        keywords = extract_keywords(text)
        print(f"文本: {text}")
        print(f"提取关键词: {keywords}")
        # 按话题分组
        topics_found = {}
        for kw in keywords:
            topic = KEYWORD_TO_TOPIC.get(kw)
            if topic:
                topics_found[topic] = topics_found.get(topic, 0) + 1
        print(f"话题分布: {topics_found}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            analyze_latest_memory()
        elif command == "reset":
            reset_topic_counter()
        elif command == "status":
            show_topic_status()
        elif command == "test":
            test_keyword_extraction()
        else:
            print("用法: python3 topic_detector_v2.py [check|reset|status|test]")
    else:
        # 默认执行检查
        analyze_latest_memory()