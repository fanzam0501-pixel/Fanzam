#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金银价格监控 - 简化稳定版
"""

import requests
import json
from datetime import datetime

def get_gold_silver_prices():
    """获取金银价格数据"""
    prices = {}
    
    # 1. 黄金ETF实时数据 (东方财富)
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": "1.518880",  # 黄金ETF
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170"
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100  # 价格需要除以100
            change_pct = d.get('f170', 0) / 100  # 涨跌幅
            prices['gold_etf'] = {
                'name': '黄金ETF(518880)',
                'price': round(price, 3),
                'change_pct': round(change_pct, 2)
            }
    except Exception as e:
        pass
    
    # 2. 白银LOF实时数据
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": "0.161226",  # 白银基金LOF
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170"
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100
            change_pct = d.get('f170', 0) / 100
            prices['silver_lof'] = {
                'name': '白银基金(161226)',
                'price': round(price, 3),
                'change_pct': round(change_pct, 2)
            }
    except:
        pass
    
    # 3. 上海黄金T+D (使用新浪财经)
    try:
        url = "https://hq.sinajs.cn/list=hf_AUTD"
        headers = {'Referer': 'https://finance.sina.com.cn'}
        r = requests.get(url, headers=headers, timeout=10)
        # 数据格式: var hq_hf_AUTD="时间,买价,最新价,卖价,最高,最低,昨收,开盘价,持仓量,买量,卖量;
        text = r.text
        if '"' in text:
            data = text.split('"')[1].split(',')
            if len(data) >= 7:
                price = float(data[2])
                prev_close = float(data[6])
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                prices['au_td'] = {
                    'name': '黄金T+D',
                    'price': round(price, 2),
                    'change_pct': round(change_pct, 2)
                }
    except:
        pass
    
    # 4. 白银T+D
    try:
        url = "https://hq.sinajs.cn/list=hf_AGTD"
        headers = {'Referer': 'https://finance.sina.com.cn'}
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text
        if '"' in text:
            data = text.split('"')[1].split(',')
            if len(data) >= 7:
                price = float(data[2])
                prev_close = float(data[6])
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                prices['ag_td'] = {
                    'name': '白银T+D',
                    'price': round(price, 0),
                    'change_pct': round(change_pct, 2)
                }
    except:
        pass
    
    # 5. 国际金价（美元）
    try:
        # 使用东方财富的美股期货数据
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": "103.GLNC",  # COMEX黄金
            "fields": "f43,f170"
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100
            change_pct = d.get('f170', 0) / 100
            prices['gold_usd'] = {
                'name': 'COMEX黄金',
                'price': round(price, 2),
                'change_pct': round(change_pct, 2)
            }
    except:
        pass
    
    # 6. 国际银价
    try:
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": "103.SILC",  # COMEX白银
            "fields": "f43,f170"
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100
            change_pct = d.get('f170', 0) / 100
            prices['silver_usd'] = {
                'name': 'COMEX白银',
                'price': round(price, 3),
                'change_pct': round(change_pct, 2)
            }
    except:
        pass
    
    return prices

def generate_report(prices):
    """生成金银价格报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report = f"""
╔══════════════════════════════════════════════════╗
║           💰 金银价格日报 - {now}           ║
╚══════════════════════════════════════════════════╝
"""
    
    # 国内品种
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    国内金银
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    has_domestic = False
    
    if 'au_td' in prices:
        p = prices['au_td']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10,.2f} 元/克    {p['change_pct']:>+.2f}%\n"
        has_domestic = True
    
    if 'ag_td' in prices:
        p = prices['ag_td']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10,.0f} 元/千克  {p['change_pct']:>+.2f}%\n"
        has_domestic = True
    
    if not has_domestic:
        report += "    (数据获取中...)\n"
    
    # ETF/LOF
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    ETF基金
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    has_etf = False
    
    if 'gold_etf' in prices:
        p = prices['gold_etf']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10.3f} 元/份    {p['change_pct']:>+.2f}%\n"
        has_etf = True
    
    if 'silver_lof' in prices:
        p = prices['silver_lof']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10.3f} 元/份    {p['change_pct']:>+.2f}%\n"
        has_etf = True
    
    if not has_etf:
        report += "    (数据获取中...)\n"
    
    # 国际品种
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    国际金银
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    has_intl = False
    
    if 'gold_usd' in prices:
        p = prices['gold_usd']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10.2f} 美元/盎司 {p['change_pct']:>+.2f}%\n"
        has_intl = True
    
    if 'silver_usd' in prices:
        p = prices['silver_usd']
        emoji = "🟢" if p['change_pct'] >= 0 else "🔴"
        report += f"{emoji} {p['name']:12} {p['price']:>10.3f} 美元/盎司 {p['change_pct']:>+.2f}%\n"
        has_intl = True
    
    if not has_intl:
        report += "    (数据获取中...)\n"
    
    # 金银比
    if 'gold_usd' in prices and 'silver_usd' in prices:
        gold_price = prices['gold_usd']['price']
        silver_price = prices['silver_usd']['price']
        if silver_price > 0:
            ratio = gold_price / silver_price
            report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    金银比参考
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 当前金银比: {ratio:.1f} : 1
💡 历史均值60-80，低于60银被低估，高于80金被低估
"""
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    市场观点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 影响因素:
   • 美联储利率政策（降息→利好黄金）
   • 美元指数走势（负相关）
   • 地缘政治风险（避险需求↑）
   • 实际利率水平（负相关）

💡 操作建议:
   • 黄金ETF(518880): 适合长期定投，抗通胀
   • 白银基金(161226): 波动更大，适合波段
   • 实物金条: 适合避险，但流动性差
   
⚠️ 风险提示:
   • 贵金属波动较大，建议分批建仓
   • 单笔仓位不超过总资产10%
   • 关注美联储议息会议纪要

╔══════════════════════════════════════════════════╗
║      ⚠️ 本报告仅供参考，不构成投资建议        ║
╚══════════════════════════════════════════════════╝
"""
    
    return report

def main():
    prices = get_gold_silver_prices()
    report = generate_report(prices)
    print(report)
    return prices

if __name__ == "__main__":
    main()
