#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析任务处理器
被 cron 调用，生成详细日报并通过消息推送
"""

import json
import requests
from datetime import datetime, timedelta
import os

class StockAnalyzer:
    def __init__(self, report_type="盘前"):
        self.report_type = report_type
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.now = datetime.now()
        
    def get_index_data(self):
        """获取主要指数数据 - 使用腾讯财经API"""
        # 腾讯财经代码格式
        indices = {
            'sh000001': '上证指数',
            'sz399001': '深证成指', 
            'sz399006': '创业板指',
            'sh000016': '上证50',
            'sh000905': '中证500'
        }
        
        # 转换为腾讯格式
        tencent_codes = []
        for code in indices.keys():
            if code.startswith('sh'):
                tencent_codes.append('sh' + code[2:])
            else:
                tencent_codes.append('sz' + code[2:])
        
        try:
            url = f"https://qt.gtimg.cn/q={','.join(tencent_codes)}"
            response = requests.get(url, timeout=10)
            response.encoding = 'gbk'
            
            results = {}
            lines = response.text.strip().split(';')
            
            for i, (code, name) in enumerate(indices.items()):
                if i < len(lines):
                    line = lines[i].strip()
                    if '="' in line:
                        data = line.split('="')[1].rstrip('"').split('~')
                        if len(data) > 45:
                            # 腾讯数据格式: ~分隔
                            # data[2]=名称, data[3]=代码, data[4]=当前价, data[5]=昨收, data[6]=今开
                            # data[7]=最高, data[8]=最低, data[9]=成交量(手), data[45]=涨跌幅%
                            current = float(data[3]) if data[3] else 0
                            prev = float(data[4]) if data[4] else 0
                            change_pct = float(data[43]) if len(data) > 43 and data[43] else 0
                            change = current - prev if prev > 0 else 0
                            
                            results[name] = {
                                'code': code,
                                'current': current,
                                'change': change,
                                'change_pct': change_pct,
                                'open': float(data[5]) if data[5] else 0,
                                'high': float(data[6]) if data[6] else 0,
                                'low': float(data[7]) if data[7] else 0,
                                'volume': float(data[9]) / 100000000 if data[9] else 0,  # 亿
                            }
            return results if results else {"error": "数据解析为空"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_north_flow(self):
        """获取北向资金流向"""
        try:
            # 使用东方财富数据接口
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': '90.HKHSGT',  # 港股通
                'fields': 'f43,f44,f45,f46,f47,f48,f50,f57,f60'
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' in data and data['data']:
                return {
                    'inflow': data['data'].get('f50', 0),  # 净流入
                    'status': '持续流入' if data['data'].get('f50', 0) > 0 else '流出'
                }
        except:
            pass
        return None
    
    def analyze_trend(self, index_data):
        """趋势分析"""
        if "error" in index_data:
            return "数据获取异常", "观望"
        
        # 简单趋势判断
        up_count = sum(1 for v in index_data.values() if isinstance(v, dict) and v.get('change', 0) > 0)
        down_count = sum(1 for v in index_data.values() if isinstance(v, dict) and v.get('change', 0) < 0)
        
        if up_count > down_count + 1:
            return "多头占优", "偏多"
        elif down_count > up_count + 1:
            return "空头占优", "偏空"
        else:
            return "震荡分化", "中性"
    
    def get_hot_sectors(self):
        """热门板块（示例，实际需要爬取）"""
        sectors = [
            ("人工智能/AI", "🔥🔥🔥", "ChatGPT、AIGC持续活跃，关注应用端落地"),
            ("中特估", "🔥🔥", "国企改革+高分红，估值修复行情"),
            ("新能源", "🔥", "光伏、储能政策利好，超跌反弹"),
            ("半导体", "📊", "周期见底预期，设备材料先行"),
            ("医药", "📉", "集采常态化，创新药分化"),
        ]
        return sectors
    
    def get_stock_picks(self):
        """选股池（示例框架）"""
        picks = {
            "短线强势股": {
                "特征": "突破平台、量价齐升、主力资金流入",
                "关注": "涨停基因、题材纯正、流通盘适中",
                "风控": "跌破5日线离场，单笔亏损不超过5%"
            },
            "趋势中军": {
                "特征": "均线多头排列、业绩稳定增长",
                "关注": "行业龙头、ROE>15%、机构抱团",
                "风控": "跌破20日线减仓，-10%止损"
            },
            "价值潜伏": {
                "特征": "低估值、高股息、护城河深",
                "关注": "PE<20、PB<3、股息率>3%",
                "风控": "分批建仓，长期持有为主"
            }
        }
        return picks
    
    def generate_market_sentiment(self):
        """市场情绪研判"""
        weekday = self.now.weekday()
        hour = self.now.hour
        
        # 简单的情绪判断逻辑
        sentiment_factors = []
        
        if self.report_type == "盘前":
            sentiment_factors.append("隔夜美股走势")
            sentiment_factors.append("外围消息面")
            sentiment_factors.append("昨日涨停家数")
        else:
            sentiment_factors.append("今日涨跌家数比")
            sentiment_factors.append("涨停/跌停比")
            sentiment_factors.append("北向资金流向")
        
        return sentiment_factors
    
    def create_report(self):
        """生成完整报告"""
        index_data = self.get_index_data()
        trend_desc, sentiment = self.analyze_trend(index_data)
        sectors = self.get_hot_sectors()
        picks = self.get_stock_picks()
        
        # 构建报告
        lines = [
            "╔" + "═" * 46 + "╗",
            "║" + f"📊 股票日报 ({self.report_type}) - {self.report_date}".center(44) + "║",
            "╚" + "═" * 46 + "╝",
            "",
            f"【⏰ 报告时间】{self.now.strftime('%H:%M')}",
            f"【📈 市场情绪】{sentiment} | {trend_desc}",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "                    大盘数据",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]
        
        # 指数数据
        if "error" not in index_data:
            for name, data in index_data.items():
                if isinstance(data, dict):
                    emoji = "🟢" if data['change_pct'] > 0 else "🔴" if data['change_pct'] < 0 else "⚪"
                    lines.append(f"{emoji} {name:8s} {data['current']:>8.2f}  {data['change']:>+7.2f} ({data['change_pct']:>+5.2f}%)")
        else:
            lines.append("⚠️ 数据获取失败，请检查网络连接")
        
        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "                    热门板块",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])
        
        # 板块数据
        for name, heat, note in sectors:
            lines.append(f"{heat} {name:10s} │ {note}")
        
        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "                    选股策略",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ])
        
        # 选股策略
        for style, info in picks.items():
            lines.append(f"▶ {style}")
            lines.append(f"  特征: {info['特征']}")
            lines.append(f"  关注: {info['关注']}")
            lines.append(f"  风控: {info['风控']}")
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "                    操作建议",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"• 仓位建议: {'6-8成（积极）' if sentiment == '偏多' else '3-5成（谨慎）' if sentiment == '偏空' else '5成（平衡）'}",
            f"• 操作风格: {'短线激进' if sentiment == '偏多' else '防守观望' if sentiment == '偏空' else '高抛低吸'}",
            "• 关注方向:",
            "  - 政策催化：人工智能、数字经济",
            "  - 业绩主线：中报预增、困境反转",
            "  - 防御配置：高股息、黄金、债券",
            "",
            "⚠️ 风险提示:",
            "  1. 控制单笔仓位，不超过总资金20%",
            "  2. 严格止损，短线-5%、中线-10%、长线-20%",
            "  3. 避免追涨杀跌，注重盈亏比",
            "  4. 关注外围市场及政策面变化",
            "",
            "╔" + "═" * 46 + "╗",
            "║" + "⚠️ 免责声明：本报告仅供参考，不构成投资建议".center(40) + "║",
            "║" + "   股市有风险，入市需谨慎".center(40) + "║",
            "╚" + "═" * 46 + "╝"
        ])
        
        return "\n".join(lines)
    
    def save_and_notify(self, report):
        """保存报告并输出"""
        # 保存到文件
        report_dir = "/root/.openclaw/workspace/stock_reports"
        os.makedirs(report_dir, exist_ok=True)
        
        filename = f"{report_dir}/report_{self.report_date}_{self.report_type}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return report

def main():
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else "盘前"
    
    analyzer = StockAnalyzer(report_type)
    report = analyzer.create_report()
    analyzer.save_and_notify(report)
    
    print(report)

if __name__ == "__main__":
    main()
