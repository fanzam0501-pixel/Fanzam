#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短线股票监控系统
实时监控持仓/关注股票，触发预警时推送提醒
"""

import json
import requests
import os
from datetime import datetime, time

class StockMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.alert_history = {}
        self.data_file = "/root/.openclaw/workspace/stock_monitor_data.json"
        self.load_history()
        
    def load_config(self):
        """加载监控配置"""
        try:
            with open('/root/.openclaw/workspace/stock_monitor_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"watchlist": [], "monitoring": {"enabled": False}}
    
    def load_history(self):
        """加载历史警报记录（防止重复提醒）"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.alert_history = json.load(f)
        except:
            self.alert_history = {}
    
    def save_history(self):
        """保存警报历史"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
    
    def is_market_hours(self):
        """判断是否为交易时间（A股+港股）"""
        if not self.config.get('monitoring', {}).get('market_hours_only', True):
            return True
        
        now = datetime.now()
        weekday = now.weekday()
        if weekday >= 5:  # 周末
            return False
        
        current_time = now.time()
        
        # A股交易时间: 9:30-11:30, 13:00-15:00
        a_share_morning = time(9, 30) <= current_time <= time(11, 30)
        a_share_afternoon = time(13, 0) <= current_time <= time(15, 0)
        a_share_hours = a_share_morning or a_share_afternoon
        
        # 港股交易时间: 9:30-12:00, 13:00-16:00
        hk_morning = time(9, 30) <= current_time <= time(12, 0)
        hk_afternoon = time(13, 0) <= current_time <= time(16, 0)
        hk_hours = hk_morning or hk_afternoon
        
        # 监控A股或港股时，在对应交易时间返回True
        has_hk = any(s['code'].startswith('hk') for s in self.config.get('watchlist', []))
        has_a = any(s['code'].startswith(('sh', 'sz')) for s in self.config.get('watchlist', []))
        
        if has_a and has_hk:
            return a_share_hours or hk_hours
        elif has_hk:
            return hk_hours
        else:
            return a_share_hours
    
    def get_realtime_quotes(self, codes):
        """获取实时行情 - 腾讯财经API (支持A股+港股)"""
        if not codes:
            return {}
        
        # 区分A股和港股代码
        a_codes = [c for c in codes if c.startswith(('sh', 'sz'))]
        hk_codes = [c for c in codes if c.startswith('hk')]
        
        all_results = {}
        
        try:
            # 获取行情数据（A股+港股一起请求）
            all_codes = a_codes + hk_codes
            url = f"https://qt.gtimg.cn/q={','.join(all_codes)}"
            response = requests.get(url, timeout=10)
            response.encoding = 'gbk'
            
            lines = response.text.strip().split(';')
            for line in lines:
                line = line.strip()
                if '="' in line and line.startswith('v_'):
                    # 解析代码，如 v_sh000001= 或 v_hkHSI=
                    code_part = line.split('="')[0]
                    code = code_part[2:] if code_part.startswith('v_') else ''  # 去掉 v_ 前缀
                    data = line.split('="')[1].rstrip('"').split('~')
                    
                    if len(data) > 45:
                        name = data[1]
                        current = float(data[3]) if data[3] else 0
                        prev_close = float(data[4]) if data[4] else 0
                        open_price = float(data[5]) if data[5] else 0
                        high = float(data[6]) if data[6] else 0
                        low = float(data[7]) if data[7] else 0
                        
                        # A股和港股成交量单位不同
                        if code.startswith('hk'):
                            volume = float(data[9]) / 1000000 if data[9] else 0  # 港股：百万股
                            market = '港股'
                        else:
                            volume = float(data[9]) / 10000 if data[9] else 0  # A股：万手
                            market = 'A股'
                        
                        change = current - prev_close
                        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                        # 振幅计算：使用开盘价作为基准更稳定
                        base_price = open_price if open_price > 0 else prev_close
                        amplitude = ((high - low) / base_price * 100) if base_price > 0 else 0
                        # 限制异常值
                        amplitude = min(amplitude, 20) if amplitude > 0 else 0
                        
                        all_results[code] = {
                            'name': name,
                            'current': current,
                            'open': open_price,
                            'high': high,
                            'low': low,
                            'prev_close': prev_close,
                            'change': change,
                            'change_pct': change_pct,
                            'volume': volume,
                            'amplitude': amplitude,
                            'market': market
                        }
            
            return all_results
        except Exception as e:
            return {"error": str(e)}
    
    def check_alerts(self, stock_data, config):
        """检查是否触发预警条件"""
        alerts = []
        code = config['code']
        alerts_config = config.get('alerts', {})
        
        if code not in stock_data:
            return alerts
        
        data = stock_data[code]
        current = data['current']
        change_pct = data['change_pct']
        
        # 检查价格突破（只在上扬时触发）
        if 'price_above' in alerts_config and current >= alerts_config['price_above'] and change_pct > 0:
            key = f"{code}_price_above"
            if not self.is_recently_alerted(key):
                alerts.append({
                    'type': 'price_breakout',
                    'level': 'important',
                    'message': f"🚀 {data['name']}({code}) 突破 {alerts_config['price_above']}元！",
                    'detail': f"当前价: {current:.2f}元，涨幅: {change_pct:+.2f}%",
                    'key': key
                })
        
        # 检查价格跌破（只在下跌时触发）
        if 'price_below' in alerts_config and current <= alerts_config['price_below'] and change_pct < 0:
            key = f"{code}_price_below"
            if not self.is_recently_alerted(key):
                alerts.append({
                    'type': 'price_breakdown',
                    'level': 'warning',
                    'message': f"⚠️ {data['name']}({code}) 跌破 {alerts_config['price_below']}元！",
                    'detail': f"当前价: {current:.2f}元，跌幅: {change_pct:+.2f}%",
                    'key': key
                })
        
        # 检查涨跌幅预警
        if 'change_pct_above' in alerts_config and change_pct >= alerts_config['change_pct_above']:
            key = f"{code}_up_{int(change_pct)}"
            if not self.is_recently_alerted(key, minutes=30):  # 涨幅预警30分钟内不重复
                alerts.append({
                    'type': 'surge',
                    'level': 'opportunity',
                    'message': f"🔥 {data['name']}({code}) 大涨 {change_pct:+.2f}%！",
                    'detail': f"当前价: {current:.2f}元，成交量: {data['volume']:.0f}万手，振幅: {data['amplitude']:.2f}%",
                    'key': key,
                    'action': '短线关注，观察是否追涨'
                })
        
        if 'change_pct_below' in alerts_config and change_pct <= alerts_config['change_pct_below']:
            key = f"{code}_down_{int(abs(change_pct))}"
            if not self.is_recently_alerted(key, minutes=30):
                alerts.append({
                    'type': 'plunge',
                    'level': 'danger',
                    'message': f"📉 {data['name']}({code}) 大跌 {change_pct:+.2f}%！",
                    'detail': f"当前价: {current:.2f}元，成交量: {data['volume']:.0f}万手",
                    'key': key,
                    'action': '注意止损，或观察抄底机会'
                })
        
        # 短线交易信号
        if abs(change_pct) > 3 and data['amplitude'] > 5:
            key = f"{code}_volatile"
            if not self.is_recently_alerted(key, minutes=60):
                signal = "强势" if change_pct > 0 else "弱势"
                alerts.append({
                    'type': 'volatile',
                    'level': 'info',
                    'message': f"📊 {data['name']} 短线{signal}，振幅 {data['amplitude']:.2f}%",
                    'detail': f"涨跌: {change_pct:+.2f}%，适合短线交易",
                    'key': key,
                    'action': '关注分时图，寻找买卖点'
                })
        
        return alerts
    
    def is_recently_alerted(self, key, minutes=60):
        """检查是否最近已提醒过（避免重复推送）"""
        if key not in self.alert_history:
            return False
        
        last_time = datetime.fromisoformat(self.alert_history[key])
        elapsed = (datetime.now() - last_time).total_seconds() / 60
        
        return elapsed < minutes
    
    def record_alert(self, key):
        """记录警报时间"""
        self.alert_history[key] = datetime.now().isoformat()
    
    def generate_short_term_signals(self, stock_data):
        """生成短线交易信号"""
        signals = []
        
        for code, data in stock_data.items():
            if 'error' in data:
                continue
            
            change_pct = data['change_pct']
            amplitude = data['amplitude']
            
            # 短线买点信号
            if -5 < change_pct < -2 and amplitude > 3:
                signals.append({
                    'code': code,
                    'name': data['name'],
                    'signal': '潜在买点',
                    'reason': f'回调 {change_pct:.2f}%，振幅 {amplitude:.2f}%，可能反弹',
                    'price': data['current']
                })
            
            # 短线卖点信号
            elif change_pct > 5 and amplitude > 4:
                signals.append({
                    'code': code,
                    'name': data['name'],
                    'signal': '获利了结',
                    'reason': f'大涨 {change_pct:.2f}%，考虑减仓锁定利润',
                    'price': data['current']
                })
            
            # 涨停/跌停监控
            if change_pct > 9.5:
                signals.append({
                    'code': code,
                    'name': data['name'],
                    'signal': '涨停',
                    'reason': '强势涨停，明日可能继续冲高',
                    'price': data['current']
                })
            elif change_pct < -9.5:
                signals.append({
                    'code': code,
                    'name': data['name'],
                    'signal': '跌停',
                    'reason': '跌停，注意风险，明日可能低开',
                    'price': data['current']
                })
        
        return signals
    
    def run(self):
        """运行监控"""
        if not self.config.get('monitoring', {}).get('enabled', False):
            return None
        
        if not self.is_market_hours():
            return "📅 非交易时间，监控暂停"
        
        watchlist = self.config.get('watchlist', [])
        if not watchlist:
            return "⚠️ 监控列表为空，请在 stock_monitor_config.json 中添加股票"
        
        codes = [s['code'] for s in watchlist]
        stock_data = self.get_realtime_quotes(codes)
        
        if 'error' in stock_data:
            return f"❌ 数据获取失败: {stock_data['error']}"
        
        all_alerts = []
        
        # 检查每只股票的预警
        for stock_config in watchlist:
            alerts = self.check_alerts(stock_data, stock_config)
            for alert in alerts:
                all_alerts.append(alert)
                self.record_alert(alert['key'])
        
        self.save_history()
        
        # 生成短线信号
        short_signals = self.generate_short_term_signals(stock_data)
        
        # 构建报告
        return self.build_report(stock_data, all_alerts, short_signals)
    
    def build_report(self, stock_data, alerts, short_signals):
        """构建监控报告"""
        lines = [
            "╔" + "═" * 50 + "╗",
            "║" + f"📈 短线监控报告 - {datetime.now().strftime('%H:%M')}".center(48) + "║",
            "╚" + "═" * 50 + "╝",
            ""
        ]
        
        # 预警信息
        if alerts:
            lines.append("🚨 【预警提醒】")
            for alert in alerts:
                emoji = "🔴" if alert['level'] == 'danger' else "🟠" if alert['level'] == 'warning' else "🟢" if alert['level'] == 'opportunity' else "🔵"
                lines.append(f"{emoji} {alert['message']}")
                lines.append(f"   {alert['detail']}")
                if 'action' in alert:
                    lines.append(f"   💡 建议: {alert['action']}")
                lines.append("")
        else:
            lines.append("✅ 暂无预警，市场平稳运行")
            lines.append("")
        
        # 短线信号
        if short_signals:
            lines.append("📊 【短线交易信号】")
            for sig in short_signals[:5]:  # 最多显示5条
                emoji = "🟢" if '买' in sig['signal'] or '涨停' in sig['signal'] else "🔴" if '卖' in sig['signal'] or '跌停' in sig['signal'] else "🟡"
                lines.append(f"{emoji} {sig['name']}({sig['code']}) - {sig['signal']}")
                lines.append(f"   价格: {sig['price']:.2f} | {sig['reason']}")
            lines.append("")
        
        # 持仓/关注列表概览
        lines.append("📋 【监控列表概览】")
        for code, data in stock_data.items():
            if 'error' not in data:
                emoji = "🟢" if data['change_pct'] > 0 else "🔴" if data['change_pct'] < 0 else "⚪"
                lines.append(f"{emoji} {data['name'][:8]:8s} {data['current']:>8.2f} ({data['change_pct']:>+5.2f}%)")
        
        lines.extend([
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "💡 短线交易策略:",
            "   • 突破追涨：放量突破前高，设止损-5%",
            "   • 回调低吸：强势股回调至5/10日线",
            "   • 严格止损：单笔亏损不超过本金的2%",
            "   • 快速止盈：盈利3-5%可考虑减仓",
            ""
        ])
        
        return "\n".join(lines)

def main():
    monitor = StockMonitor()
    result = monitor.run()
    print(result if result else "监控运行完成，无新预警")

if __name__ == "__main__":
    main()
