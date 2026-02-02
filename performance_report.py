#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统性能报告生成器
"""

import os
import subprocess
import json
from datetime import datetime

def get_system_stats():
    """获取系统统计 - 使用系统命令"""
    # 内存信息
    mem_info = subprocess.run(['free', '-m'], capture_output=True, text=True)
    mem_lines = mem_info.stdout.strip().split('\n')
    if len(mem_lines) >= 2:
        mem_data = mem_lines[1].split()
        total_mb = int(mem_data[1])
        used_mb = int(mem_data[2])
        mem_percent = int(used_mb / total_mb * 100)
    else:
        total_mb = used_mb = mem_percent = 0
    
    # 磁盘信息
    disk_info = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    disk_lines = disk_info.stdout.strip().split('\n')
    if len(disk_lines) >= 2:
        disk_data = disk_lines[1].split()
        disk_total = disk_data[1]
        disk_used = disk_data[2]
        disk_percent = int(disk_data[4].replace('%', ''))
    else:
        disk_total = disk_used = "0G"
        disk_percent = 0
    
    # CPU信息
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
            fields = line.split()
            if len(fields) > 4:
                user = int(fields[1])
                nice = int(fields[2])
                system = int(fields[3])
                idle = int(fields[4])
                total = user + nice + system + idle
                cpu = int((total - idle) / total * 100) if total > 0 else 0
            else:
                cpu = 0
    except:
        cpu = 0
    
    return {
        'memory': {
            'total': f"{total_mb / 1024:.1f}GB",
            'used': f"{used_mb / 1024:.1f}GB",
            'percent': mem_percent
        },
        'disk': {
            'total': disk_total,
            'used': disk_used,
            'percent': disk_percent
        },
        'cpu': cpu
    }

def get_openclaw_stats():
    """获取OpenClaw进程统计 - 使用ps命令"""
    processes = []
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'openclaw' in line.lower() and 'grep' not in line.lower():
                parts = line.split()
                if len(parts) >= 11:
                    pid = parts[1]
                    mem = parts[3]  # %MEM
                    name = parts[10][:20]
                    processes.append({
                        'name': name,
                        'pid': pid,
                        'memory': f"{mem}%"
                    })
    except:
        pass
    return processes

def get_cron_stats():
    """获取定时任务统计"""
    try:
        result = subprocess.run(['openclaw', 'cron', 'list'], 
                              capture_output=True, text=True)
        return len([l for l in result.stdout.split('\n') if 'jobId' in l])
    except:
        return 0

def generate_report():
    """生成性能报告"""
    print("=" * 50)
    print(f"📊 OpenClaw 性能报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    stats = get_system_stats()
    
    print("\n🖥️  系统资源:")
    print(f"  CPU使用: {stats['cpu']}%")
    print(f"  内存: {stats['memory']['used']} / {stats['memory']['total']} ({stats['memory']['percent']}%)")
    print(f"  磁盘: {stats['disk']['used']} / {stats['disk']['total']} ({stats['disk']['percent']}%)")
    
    print("\n🔧 OpenClaw进程:")
    processes = get_openclaw_stats()
    for p in processes:
        print(f"  {p['name']}: PID={p['pid']}, MEM={p['memory']}")
    
    print(f"\n⏰ 定时任务: {get_cron_stats()} 个")
    
    # 性能评级
    print("\n📈 性能评级:")
    mem_percent = stats['memory']['percent']
    if mem_percent < 70:
        print("  🟢 良好 - 系统运行流畅")
    elif mem_percent < 85:
        print("  🟡 一般 - 建议优化内存")
    else:
        print("  🔴 紧张 - 需要立即优化")
    
    print("\n💡 建议:")
    if mem_percent > 85:
        print("  1. 运行: bash optimize_system.sh")
        print("  2. 考虑重启OpenClaw: openclaw gateway restart")
    if stats['disk']['percent'] > 80:
        print("  3. 磁盘空间不足，清理日志文件")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    generate_report()
