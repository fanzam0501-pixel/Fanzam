#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能金价监控系统
- 每日8:00晨报
- 每30分钟趋势分析
- 峰顶转下滑/谷底转上升提醒
- 持续下跌不反馈
"""

import json
import requests
import os
import sys
from datetime import datetime, timedelta
from collections import deque

class GoldPriceMonitor:
    def __init__(self, mode="analysis"):
        self.mode = mode  # 'morning_report' 或 'analysis'
        self.config = self._load_config()
        self.history = self._load_history()
        self.state = self._load_state()
        self.now = datetime.now()

    def _load_config(self):
        """加载配置"""
        try:
            with open('/root/.openclaw/workspace/gold_monitor_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"配置加载失败: {e}")
            return {}

    def _load_history(self):
        """加载价格历史"""
        history_file = self.config.get('gold_monitoring', {}).get('history_file',
                      '/root/.openclaw/workspace/gold_price_history.json')
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_history(self):
        """保存价格历史"""
        history_file = self.config.get('gold_monitoring', {}).get('history_file',
                      '/root/.openclaw/workspace/gold_price_history.json')
        try:
            with open(history_file, 'w') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"历史保存失败: {e}")

    def _load_state(self):
        """加载监控状态"""
        state_file = self.config.get('gold_monitoring', {}).get('state_file',
                     '/root/.openclaw/workspace/gold_monitor_state.json')
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            return {"trend": "unknown", "last_alert": None, "last_price": None}

    def _save_state(self):
        """保存监控状态"""
        state_file = self.config.get('gold_monitoring', {}).get('state_file',
                     '/root/.openclaw/workspace/gold_monitor_state.json')
        try:
            with open(state_file, 'w') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"状态保存失败: {e}")

    def get_gold_price_huilvbiao(self):
        """从汇率表网站获取黄金T+D价格（国内金价）"""
        try:
            url = "https://www.huilvbiao.com/api/gold_autd_real"
            params = {
                't': 'au9',  # au9 = AU9999/T+D
                '_': int(datetime.now().timestamp())
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.huilvbiao.com/gold/au9999'
            }
            response = requests.get(url, params=params, headers=headers, timeout=15)
            data = response.json()

            if data and len(data) > 0:
                # 取最新一条数据
                latest = data[0]
                current = float(latest['new'])
                prev_close = float(latest['buy'])  # 用买入价作为昨收参考
                change_pct = float(latest['diffper'])

                return {
                    'name': '国内金价(AU9999/T+D)',
                    'current': current,
                    'open': float(latest['open']),
                    'high': float(latest['high']),
                    'low': float(latest['low']),
                    'prev_close': prev_close,
                    'change': current - prev_close,
                    'change_pct': change_pct,
                    'buy_price': float(latest['buy']),
                    'sell_price': float(latest['sell']),
                    'update_time': latest.get('date_time', self.now.strftime('%H:%M:%S')),
                    'source': '汇率表(huilvbiao.com)'
                }
        except Exception as e:
            print(f"汇率表金价获取失败: {e}")
        return None

    def get_gold_price_tencent(self):
        """从腾讯财经获取黄金ETF价格"""
        try:
            url = "https://qt.gtimg.cn/q=sh518880"
            response = requests.get(url, timeout=10)
            response.encoding = 'gbk'

            data = response.text
            if '="' in data:
                parts = data.split('="')[1].rstrip('";').split('~')
                if len(parts) > 45:
                    current = float(parts[3])
                    prev = float(parts[4])
                    change_pct = float(parts[43]) if parts[43] else 0
                    return {
                        'name': '黄金ETF(518880)',
                        'current': current,
                        'open': float(parts[5]),
                        'high': float(parts[33]) if len(parts) > 33 else float(parts[6]),
                        'low': float(parts[34]) if len(parts) > 34 else float(parts[7]),
                        'prev_close': prev,
                        'change': current - prev,
                        'change_pct': change_pct,
                        'volume': float(parts[9]) / 10000 if parts[9] else 0,
                        'update_time': self.now.strftime('%H:%M:%S')
                    }
        except Exception as e:
            print(f"黄金ETF数据获取失败: {e}")
        return None

    def get_all_prices(self):
        """获取国内金价数据（同时获取黄金ETF和AU9999）"""
        prices = {}

        # 从汇率表获取国内金价（黄金T+D/AU9999）
        huilvbiao_data = self.get_gold_price_huilvbiao()
        if huilvbiao_data:
            prices['AU9999'] = huilvbiao_data

        # 从腾讯获取黄金ETF
        etf_data = self.get_gold_price_tencent()
        if etf_data:
            prices['518880'] = etf_data

        return prices

    def update_history(self, prices):
        """更新价格历史"""
        timestamp = self.now.strftime('%Y-%m-%d %H:%M')
        date_key = self.now.strftime('%Y-%m-%d')

        if date_key not in self.history:
            self.history[date_key] = []

        # 添加新记录
        record = {
            'timestamp': timestamp,
            'prices': {k: v['current'] for k, v in prices.items()},
            'change_pct': {k: v.get('change_pct', 0) for k, v in prices.items()}
        }
        self.history[date_key].append(record)

        # 只保留最近30天的数据
        dates = sorted(self.history.keys())
        if len(dates) > 30:
            for old_date in dates[:-30]:
                del self.history[old_date]

        self._save_history()

    def detect_trend_turning_point(self, symbol='AU9999'):
        """
        检测趋势转折点
        返回: ('peak_to_decline', confidence) - 峰顶转下滑
              ('valley_to_rise', confidence) - 谷底转上升
              ('continuous_decline', None) - 持续下跌
              ('none', None) - 无明确信号
        """
        date_key = self.now.strftime('%Y-%m-%d')
        if date_key not in self.history:
            return 'none', None

        day_history = self.history[date_key]
        if len(day_history) < 3:
            return 'none', None

        # 获取该品种的价格序列
        prices = []
        for record in day_history:
            if symbol in record.get('prices', {}):
                prices.append(record['prices'][symbol])

        if len(prices) < 3:
            return 'none', None

        # 计算价格变化
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # 检测峰顶转下滑：之前上升，最近下降
        if len(changes) >= 2:
            # 最近两次都是下降
            if changes[-1] < 0 and changes[-2] < 0:
                # 检查之前是否有上升
                rise_before = any(c > 0 for c in changes[:-2])
                if rise_before:
                    # 检查是否是局部峰值
                    if len(prices) >= 3 and prices[-2] > prices[-3] and prices[-2] > prices[-1]:
                        return 'peak_to_decline', abs(changes[-1] / prices[-2] * 100)

        # 检测谷底转上升：之前下降，最近上升
        if len(changes) >= 2:
            # 最近两次都是上升
            if changes[-1] > 0 and changes[-2] > 0:
                # 检查之前是否有下降
                decline_before = any(c < 0 for c in changes[:-2])
                if decline_before:
                    # 检查是否是局部谷值
                    if len(prices) >= 3 and prices[-2] < prices[-3] and prices[-2] < prices[-1]:
                        return 'valley_to_rise', abs(changes[-1] / prices[-2] * 100)

        # 检测持续下跌
        if len(changes) >= 2 and all(c < 0 for c in changes[-3:]):
            return 'continuous_decline', None

        return 'none', None

    def generate_morning_report(self, prices):
        """生成晨报"""
        lines = [
            "╔" + "═" * 46 + "╗",
            "║" + "🥇 金价晨报 - {}".format(self.now.strftime('%Y-%m-%d %H:%M')).center(42) + "║",
            "╚" + "═" * 46 + "╝",
            ""
        ]

        for symbol, data in prices.items():
            emoji = "🟢" if data['change_pct'] > 0 else "🔴" if data['change_pct'] < 0 else "⚪"
            lines.append(f"{emoji} {data['name']}")
            lines.append(f"   现价: {data['current']:.2f} ({data['change']:+.2f}, {data['change_pct']:+.2f}%)")
            lines.append(f"   最高: {data['high']:.2f} | 最低: {data['low']:.2f}")
            lines.append("")

        # 添加趋势判断
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("📊 趋势分析")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for symbol in prices.keys():
            trend, confidence = self.detect_trend_turning_point(symbol)
            symbol_name = prices[symbol]['name']

            if trend == 'peak_to_decline':
                lines.append(f"⚠️ {symbol_name}: 检测到峰顶转下滑信号")
            elif trend == 'valley_to_rise':
                lines.append(f"✅ {symbol_name}: 检测到谷底转上升信号")
            elif trend == 'continuous_decline':
                lines.append(f"📉 {symbol_name}: 持续下跌中")
            else:
                lines.append(f"📊 {symbol_name}: 趋势平稳")

        lines.append("")
        lines.append("💡 监控规则: 峰顶转下滑/谷底转上升时提醒")
        lines.append("   持续下跌期间不发送提醒")

        return "\n".join(lines)

    def generate_analysis_report(self, prices):
        """生成实时分析报告（只在转折点触发）"""
        alerts = []

        for symbol, data in prices.items():
            trend, confidence = self.detect_trend_turning_point(symbol)

            if trend == 'peak_to_decline':
                alerts.append({
                    'type': 'peak_to_decline',
                    'symbol': symbol,
                    'name': data['name'],
                    'price': data['current'],
                    'change_pct': data['change_pct'],
                    'confidence': confidence
                })
            elif trend == 'valley_to_rise':
                alerts.append({
                    'type': 'valley_to_rise',
                    'symbol': symbol,
                    'name': data['name'],
                    'price': data['current'],
                    'change_pct': data['change_pct'],
                    'confidence': confidence
                })

        if not alerts:
            return None  # 没有转折点，不发送报告

        lines = [
            "╔" + "═" * 46 + "╗",
            "║" + "🚨 金价趋势转折提醒".center(42) + "║",
            "╚" + "═" * 46 + "╝",
            f"\n⏰ {self.now.strftime('%H:%M')}\n"
        ]

        for alert in alerts:
            if alert['type'] == 'peak_to_decline':
                emoji = "🔻"
                text = f"峰顶转下滑 (置信度: {alert['confidence']:.2f}%)"
            else:
                emoji = "🔺"
                text = f"谷底转上升 (置信度: {alert['confidence']:.2f}%)"

            lines.append(f"{emoji} {alert['name']}: {text}")
            lines.append(f"   当前价格: {alert['price']:.2f}")
            lines.append(f"   涨跌幅: {alert['change_pct']:+.2f}%")
            lines.append("")

        return "\n".join(lines)

    def run(self):
        """主运行逻辑"""
        prices = self.get_all_prices()

        if not prices:
            print("❌ 未能获取金价数据")
            return None

        # 更新历史记录
        self.update_history(prices)

        if self.mode == 'morning_report':
            report = self.generate_morning_report(prices)
            print(report)
            return report
        else:
            # 分析模式：只在转折点生成报告
            report = self.generate_analysis_report(prices)
            if report:
                print(report)
                return report
            else:
                print(f"[{self.now.strftime('%H:%M')}] 趋势平稳或持续下跌，无需提醒")
                return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'analysis'
    monitor = GoldPriceMonitor(mode)
    report = monitor.run()

    # 输出标记，供外部判断是否有报告生成
    if report:
        print("\n[HAS_ALERT]")
    else:
        print("\n[NO_ALERT]")


if __name__ == "__main__":
    main()
