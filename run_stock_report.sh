#!/bin/bash
# 股票日报生成脚本 - 由 cron 调用

REPORT_TYPE="$1"
if [ -z "$REPORT_TYPE" ]; then
    REPORT_TYPE="盘前"
fi

cd /root/.openclaw/workspace

# 生成报告
python3 stock_analyzer.py "$REPORT_TYPE" > /tmp/stock_report.txt 2>&1

# 输出报告内容
cat /tmp/stock_report.txt

echo ""
echo "📄 报告已保存至: stock_reports/ 目录"
