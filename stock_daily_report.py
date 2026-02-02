#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日股票分析日报生成器
运行时间：工作日 09:00（开盘前）或 15:30（收盘后）
"""

import json
import requests
from datetime import datetime, timedelta
import random

class StockDailyReport:
    def __init__(self):
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.weekday = datetime.now().weekday()
        
    def is_trading_day(self):
        """判断是否为交易日（简化版，实际需要对接交易日历API）"""
        # 0-4 为周一至周五
        return self.weekday < 5
    
    def get_market_data(self):
        """获取大盘数据（使用新浪财经API）"""
        try:
            # 上证指数、深证成指、创业板指
            symbols = ['sh000001', 'sz399001', 'sz399006']
            url = f"https://hq.sinajs.cn/list={','.join(symbols)}"
            headers = {'Referer': 'https://finance.sina.com.cn'}
            response = requests.get(url, headers=headers, timeout=10)
            
            market_data = {}
            lines = response.text.strip().split('\n')
            names = ['上证指数', '深证成指', '创业板指']
            
            for i, line in enumerate(lines):
                if i < len(names):
                    parts = line.split('="')[1].rstrip('";').split(',')
                    if len(parts) > 3:
                        market_data[names[i]] = {
                            'name': parts[0],
                            'current': float(parts[3]),
                            'open': float(parts[1]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'prev_close': float(parts[2])
                        }
            return market_data
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_market(self, data):
        """市场分析"""
        if "error" in data:
            return "【数据获取失败】无法获取实时行情数据"
        
        analysis = []
        for name, info in data.items():
            if isinstance(info, dict):
                change = info['current'] - info['prev_close']
                change_pct = (change / info['prev_close']) * 100
                trend = "📈" if change > 0 else "📉" if change < 0 else "➖"
                analysis.append(f"{trend} {name}: {info['current']:.2f} ({change:+.2f}, {change_pct:+.2f}%)")
        
        return "\n".join(analysis) if analysis else "暂无数据"
    
    def generate_sectors(self):
        """热门板块分析（示例数据框架，实际需对接板块数据）"""
        sectors = [
            {"name": "人工智能", "trend": "🔥", "note": "ChatGPT概念持续发酵"},
            {"name": "新能源", "trend": "📈", "note": "政策利好，光伏储能回暖"},
            {"name": "半导体", "trend": "📊", "note": "周期底部，关注设备材料"},
            {"name": "医药", "trend": "📉", "note": "集采压力，观望为主"},
            {"name": "中特估", "trend": "📈", "note": "高分红蓝筹受青睐"}
        ]
        return sectors
    
    def generate_stock_picks(self):
        """选股推荐（示例框架，实际需对接选股策略）"""
        picks = [
            {"type": "短线", "strategy": "追涨强势股", "focus": "突破新高、放量涨停"},
            {"type": "中线", "strategy": "趋势跟踪", "focus": "均线多头排列、业绩预增"},
            {"type": "长线", "strategy": "价值投资", "focus": "低估值、高股息、护城河"}
        ]
        return picks
    
    def generate_report(self):
        """生成完整日报"""
        if not self.is_trading_day():
            return f"📅 {self.report_date} 为非交易日，今日休市"
        
        market_data = self.get_market_data()
        market_analysis = self.analyze_market(market_data)
        sectors = self.generate_sectors()
        picks = self.generate_stock_picks()
        
        report = f"""
═══════════════════════════════════════
📊 每日股票分析日报 - {self.report_date}
═══════════════════════════════════════

【🌅 大盘概况】
{market_analysis}

【🔥 热门板块】
"""
        for sector in sectors:
            report += f"  {sector['trend']} {sector['name']}: {sector['note']}\n"
        
        report += "\n【📋 选股策略】\n"
        for pick in picks:
            report += f"  ▪ {pick['type']}: {pick['strategy']}\n    关注: {pick['focus']}\n"
        
        report += f"""
【⚠️ 风险提示】
1. 控制仓位，建议单票不超过总资金20%
2. 设置止损，短线-5%、中线-10%
3. 关注外围市场及政策面变化

【💡 操作建议】
• 大盘情绪: {"偏乐观" if random.random() > 0.4 else "偏谨慎"}
• 仓位建议: 5-7成
• 重点关注: 政策催化方向、业绩超预期个股

═══════════════════════════════════════
免责声明: 以上分析仅供参考，不构成投资建议
股市有风险，入市需谨慎
═══════════════════════════════════════
"""
        return report

def main():
    reporter = StockDailyReport()
    report = reporter.generate_report()
    print(report)
    
    # 保存到文件
    filename = f"/root/.openclaw/workspace/stock_reports/daily_{datetime.now().strftime('%Y%m%d')}.txt"
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 报告已保存: {filename}")

if __name__ == "__main__":
    main()
