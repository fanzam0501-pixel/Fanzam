#!/usr/bin/env python3
"""
话题检测脚本
用于检测对话中的不同话题方向，并在达到阈值时触发备份
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Set

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
TOPIC_TRACKER_FILE = os.path.join(REPO_DIR, ".topic_tracker.json")
FORCE_BACKUP_FILE = os.path.join(REPO_DIR, ".force_backup_due_to_topics")
MEMORY_DIR = os.path.join(REPO_DIR, "memory")

# 话题关键词定义
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

def load_topic_tracker() -> Dict:
    """加载话题追踪器数据"""
    if os.path.exists(TOPIC_TRACKER_FILE):
        try:
            with open(TOPIC_TRACKER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # 默认数据结构
    return {
        "version": 1,
        "current_session_topics": [],  # 当前会话中检测到的话题列表
        "all_detected_topics": [],     # 历史检测到的所有话题
        "last_checked_file": "",
        "last_checked_time": 0,
        "topic_count": 0,
        "threshold": 10,               # 触发备份的话题数量阈值
        "last_reset_time": 0
    }

def save_topic_tracker(data: Dict):
    """保存话题追踪器数据"""
    with open(TOPIC_TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def detect_topics_in_text(text: str) -> List[str]:
    """从文本中检测话题"""
    detected = set()
    text_lower = text.lower()
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.add(topic)
                break
    
    return list(detected)

def get_latest_memory_file() -> str:
    """获取最新的记忆文件"""
    if not os.path.exists(MEMORY_DIR):
        return ""
    
    md_files = []
    for file in os.listdir(MEMORY_DIR):
        if file.endswith('.md'):
            file_path = os.path.join(MEMORY_DIR, file)
            md_files.append((file_path, os.path.getmtime(file_path)))
    
    if not md_files:
        return ""
    
    # 按修改时间排序，获取最新的文件
    md_files.sort(key=lambda x: x[1], reverse=True)
    return md_files[0][0]

def analyze_latest_memory() -> Set[str]:
    """分析最新的记忆文件，检测话题"""
    latest_file = get_latest_memory_file()
    if not latest_file:
        return set()
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 只分析最近的内容（最后2000字符）
        recent_content = content[-2000:]
        return set(detect_topics_in_text(recent_content))
    except (IOError, UnicodeDecodeError):
        return set()

def check_and_update_topics():
    """检查并更新话题计数"""
    tracker = load_topic_tracker()
    
    # 获取最新检测到的话题
    current_topics = analyze_latest_memory()
    
    if not current_topics:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 未检测到新话题")
        return
    
    # 检查是否有新的话题
    new_topics = []
    for topic in current_topics:
        if topic not in tracker["current_session_topics"]:
            new_topics.append(topic)
    
    if new_topics:
        # 更新话题列表
        tracker["current_session_topics"].extend(new_topics)
        tracker["current_session_topics"] = list(set(tracker["current_session_topics"]))
        tracker["topic_count"] = len(tracker["current_session_topics"])
        
        # 更新历史话题
        for topic in new_topics:
            if topic not in tracker["all_detected_topics"]:
                tracker["all_detected_topics"].append(topic)
        
        tracker["last_checked_time"] = int(datetime.now().timestamp())
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 检测到新话题: {new_topics}")
        print(f"当前话题数量: {tracker['topic_count']}/{tracker['threshold']}")
        
        # 检查是否达到阈值
        if tracker["topic_count"] >= tracker["threshold"]:
            print(f"话题数量达到阈值 {tracker['threshold']}，将触发备份")
            # 创建触发文件
            with open(FORCE_BACKUP_FILE, 'w') as f:
                f.write(f"话题数量达到阈值 {tracker['topic_count']}，触发备份")
            
            # 重置当前会话话题计数
            tracker["current_session_topics"] = []
            tracker["topic_count"] = 0
            tracker["last_reset_time"] = int(datetime.now().timestamp())
        
        save_topic_tracker(tracker)
    else:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 未检测到新话题")

def reset_topic_counter():
    """重置话题计数器"""
    tracker = load_topic_tracker()
    tracker["current_session_topics"] = []
    tracker["topic_count"] = 0
    tracker["last_reset_time"] = int(datetime.now().timestamp())
    save_topic_tracker(tracker)
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 话题计数器已重置")

def show_topic_status():
    """显示话题状态"""
    tracker = load_topic_tracker()
    print(f"=== 话题检测状态 ===")
    print(f"当前会话话题数: {tracker['topic_count']}/{tracker['threshold']}")
    print(f"当前话题: {', '.join(tracker['current_session_topics']) if tracker['current_session_topics'] else '无'}")
    print(f"历史检测话题数: {len(tracker['all_detected_topics'])}")
    print(f"最后重置时间: {datetime.fromtimestamp(tracker['last_reset_time']).strftime('%Y-%m-%d %H:%M:%S') if tracker['last_reset_time'] else '从未'}")
    print(f"最后检查时间: {datetime.fromtimestamp(tracker['last_checked_time']).strftime('%Y-%m-%d %H:%M:%S') if tracker['last_checked_time'] else '从未'}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            check_and_update_topics()
        elif command == "reset":
            reset_topic_counter()
        elif command == "status":
            show_topic_status()
        elif command == "test":
            # 测试话题检测
            test_text = "今天的股票行情怎么样？AI技术发展很快啊。"
            topics = detect_topics_in_text(test_text)
            print(f"测试文本: {test_text}")
            print(f"检测到话题: {topics}")
        else:
            print("用法: python3 topic_detector.py [check|reset|status|test]")
    else:
        # 默认执行检查
        check_and_update_topics()