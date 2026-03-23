#!/usr/bin/env python3
"""
股票盯盘配置管理
"""

import json
import os
import sys
from datetime import datetime

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(WORK_DIR, "config.json")

def load_config():
    """加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return {
            "stocks": [],
            "channels": ["feishu"],
            "targets": {},
            "price_change_threshold": 1.5
        }
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存到 {CONFIG_FILE}")

def add_stock(market: str, code: str, name: str = None, alert_up: float = None, alert_down: float = None):
    """添加监控股票"""
    config = load_config()
    
    # 检查是否已存在
    for stock in config["stocks"]:
        if stock["code"] == code and stock["market"] == market:
            print(f"⚠️ {market} {code} 已在监控列表中")
            # 更新价格提醒
            if alert_up:
                stock["alert_prices"]["up"] = alert_up
            if alert_down:
                stock["alert_prices"]["down"] = alert_down
            if name:
                stock["name"] = name
            save_config(config)
            return
    
    # 添加新股票
    stock = {
        "market": market,
        "code": code,
        "name": name or code,
        "alert_prices": {}
    }
    if alert_up:
        stock["alert_prices"]["up"] = alert_up
    if alert_down:
        stock["alert_prices"]["down"] = alert_down
    
    config["stocks"].append(stock)
    save_config(config)
    print(f"✅ 已添加: {market} {code} ({name or code})")

def remove_stock(market: str, code: str):
    """移除监控股票"""
    config = load_config()
    original_count = len(config["stocks"])
    
    config["stocks"] = [
        s for s in config["stocks"]
        if not (s["code"] == code and s["market"] == market)
    ]
    
    if len(config["stocks"]) < original_count:
        save_config(config)
        print(f"✅ 已移除: {market} {code}")
    else:
        print(f"⚠️ 未找到: {market} {code}")

def list_stocks():
    """列出所有监控股票"""
    config = load_config()
    
    if not config["stocks"]:
        print("📋 监控列表为空")
        return
    
    print("📋 监控股票列表:")
    print("-" * 60)
    for i, stock in enumerate(config["stocks"], 1):
        alerts = ""
        if stock.get("alert_prices"):
            parts = []
            if stock["alert_prices"].get("up"):
                parts.append(f"涨破{stock['alert_prices']['up']}")
            if stock["alert_prices"].get("down"):
                parts.append(f"跌破{stock['alert_prices']['down']}")
            alerts = f" | {' '.join(parts)}"
        print(f"{i}. [{stock['market']}] {stock['code']} - {stock['name']}{alerts}")
    print("-" * 60)
    print(f"共 {len(config['stocks'])} 只股票")

def set_target(channel: str, target: str):
    """设置提醒目标"""
    config = load_config()
    if "targets" not in config:
        config["targets"] = {}
    config["targets"][channel] = target
    # 只有真正的 channel 才加入 channels 列表，feishu_user 只是用于 @ 用户
    if channel not in ["feishu_user"] and channel not in config.get("channels", []):
        config["channels"] = config.get("channels", []) + [channel]
    save_config(config)
    print(f"✅ 已设置 {channel} 目标: {target}")

def show_config():
    """显示完整配置"""
    config = load_config()
    print("📋 当前配置:")
    print(json.dumps(config, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python config.py add <市场> <代码> [名称] [涨破价] [跌破价]")
        print("  python config.py remove <市场> <代码>")
        print("  python config.py list")
        print("  python config.py target <渠道> <目标>")
        print("  python config.py show")
        print()
        print("示例:")
        print("  python config.py add A股 600111 北方稀土")
        print("  python config.py add A股 600111 北方稀土 50 40  # 涨破50/跌破40提醒")
        print("  python config.py add 港股 00700 腾讯")
        print("  python config.py add 美股 AAPL 苹果")
        print("  python config.py target feishu oc_xxx")
        print("  python config.py target wechat xxx")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "add":
        market = sys.argv[2] if len(sys.argv) > 2 else "A股"
        code = sys.argv[3] if len(sys.argv) > 3 else ""
        name = sys.argv[4] if len(sys.argv) > 4 else None
        alert_up = float(sys.argv[5]) if len(sys.argv) > 5 else None
        alert_down = float(sys.argv[6]) if len(sys.argv) > 6 else None
        add_stock(market, code, name, alert_up, alert_down)
    
    elif cmd == "remove":
        market = sys.argv[2] if len(sys.argv) > 2 else "A股"
        code = sys.argv[3] if len(sys.argv) > 3 else ""
        remove_stock(market, code)
    
    elif cmd == "list":
        list_stocks()
    
    elif cmd == "target":
        channel = sys.argv[2] if len(sys.argv) > 2 else ""
        target = sys.argv[3] if len(sys.argv) > 3 else ""
        set_target(channel, target)
    
    elif cmd == "show":
        show_config()
    
    else:
        print(f"未知命令: {cmd}")