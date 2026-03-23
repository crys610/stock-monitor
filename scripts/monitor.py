#!/usr/bin/env python3
"""
多市场股票盯盘脚本
支持：A股、港股、美股
"""

import json
import requests
from datetime import datetime, time
import os
import subprocess
import fcntl
import sys

# ========== 配置 ==========
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(WORK_DIR, "config.json")
DATA_FILE = os.path.join(WORK_DIR, "data.json")
LOG_FILE = "/tmp/stock-monitor.log"

# 价格异动阈值
PRICE_CHANGE_THRESHOLD = 1.5  # 单次涨跌超过1.5%提醒

# ========== 工具函数 ==========
def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except:
        pass

def safe_read_json(filepath: str, default=None):
    if not os.path.exists(filepath):
        return default if default is not None else {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def safe_write_json(filepath: str, data: dict):
    try:
        with open(filepath, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f, ensure_ascii=False, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        log(f"JSON写入失败: {e}")

# ========== 行情获取 ==========
def get_a_stock_quote(code: str) -> dict:
    """获取A股实时行情 (新浪)"""
    prefix = "sh" if code.startswith("6") else "sz"
    symbol = f"{prefix}{code}"
    url = f"http://hq.sinajs.cn/list={symbol}"
    headers = {
        "Referer": "http://finance.sina.com.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "gbk"
        if 'hq_str_' not in resp.text:
            return None
        parts = resp.text.split('"')[1].split(',')
        if len(parts) < 10:
            return None
        open_price = float(parts[1]) if parts[1] else 0
        prev_close = float(parts[2]) if parts[2] else 0
        current = float(parts[3]) if parts[3] else 0
        return {
            "name": parts[0],
            "open": open_price,
            "prev_close": prev_close,
            "current": current,
            "high": float(parts[4]) if parts[4] else 0,
            "low": float(parts[5]) if parts[5] else 0,
            "volume": int(float(parts[8])) if parts[8] else 0,
            "amount": float(parts[9]) if parts[9] else 0,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "valid": open_price > 0 and current > 0 and prev_close > 0,
            "market": "A股"
        }
    except Exception as e:
        log(f"A股行情获取失败 {code}: {e}")
        return None

def get_hk_stock_quote(code: str) -> dict:
    """获取港股实时行情 (腾讯)"""
    # 港股代码补零到5位
    code = code.zfill(5)
    url = f"https://web.sqt.gtimg.cn/q=r_hk{code}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        # 返回格式: v_r_hk00700="51~腾讯控股~00700~..."
        if 'v_r_hk' not in resp.text:
            return None
        content = resp.text.split('"')[1]
        if not content:
            return None
        parts = content.split('~')
        if len(parts) < 10:
            return None
        current = float(parts[3]) if parts[3] else 0
        prev_close = float(parts[4]) if parts[4] else 0
        open_price = float(parts[5]) if parts[5] else 0
        return {
            "name": parts[1],
            "open": open_price,
            "prev_close": prev_close,
            "current": current,
            "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
            "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
            "volume": int(float(parts[6])) if parts[6] else 0,
            "amount": float(parts[37]) if len(parts) > 37 and parts[37] else 0,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "valid": open_price > 0 and current > 0 and prev_close > 0,
            "market": "港股"
        }
    except Exception as e:
        log(f"港股行情获取失败 {code}: {e}")
        return None

def get_us_stock_quote(code: str) -> dict:
    """获取美股实时行情 (Yahoo Finance API)"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        chart = data.get("chart", {}).get("result", [])
        if not chart:
            return None
        meta = chart[0].get("meta", {})
        current = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("previousClose", 0)
        open_price = meta.get("regularMarketOpen", 0)
        return {
            "name": meta.get("shortName", code),
            "open": open_price,
            "prev_close": prev_close,
            "current": current,
            "high": meta.get("regularMarketDayHigh", 0),
            "low": meta.get("regularMarketDayLow", 0),
            "volume": meta.get("regularMarketVolume", 0),
            "amount": 0,
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "valid": open_price > 0 and current > 0 and prev_close > 0,
            "market": "美股"
        }
    except Exception as e:
        log(f"美股行情获取失败 {code}: {e}")
        return None

def get_quote(market: str, code: str) -> dict:
    """统一行情获取接口"""
    market = market.lower()
    if market in ["a股", "a", "cn", "sh", "sz"]:
        return get_a_stock_quote(code)
    elif market in ["港股", "hk", "hongkong"]:
        return get_hk_stock_quote(code)
    elif market in ["美股", "us", "usa"]:
        return get_us_stock_quote(code)
    else:
        log(f"未知市场: {market}")
        return None

# ========== 交易时段判断 ==========
def is_trading_time(market: str) -> bool:
    """判断是否在交易时段"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    market = market.lower()
    
    if market in ["a股", "a", "cn", "sh", "sz"]:
        # A股: 工作日 9:30-11:30, 13:00-15:00
        if weekday >= 5:
            return False
        morning = time(9, 25) <= current_time <= time(11, 30)
        afternoon = time(13, 0) <= current_time <= time(15, 0)
        return morning or afternoon
    
    elif market in ["港股", "hk", "hongkong"]:
        # 港股: 工作日 9:30-12:00, 13:00-16:00 (北京时间)
        if weekday >= 5:
            return False
        morning = time(9, 25) <= current_time <= time(12, 0)
        afternoon = time(13, 0) <= current_time <= time(16, 0)
        return morning or afternoon
    
    elif market in ["美股", "us", "usa"]:
        # 美股: 北京时间 21:30-04:00 (冬令时) 或 22:30-05:00 (夏令时)
        # 简化处理: 21:00 - 次日 05:00
        hour = current_time.hour
        return hour >= 21 or hour <= 5
    
    return False

def get_time_slot(market: str) -> str:
    """返回当前时段"""
    now = datetime.now().time()
    market = market.lower()
    
    if market in ["a股", "a", "cn", "sh", "sz"]:
        if time(9, 30) <= now <= time(9, 45):
            return "morning_open"
        elif time(11, 25) <= now <= time(11, 35):
            return "morning_close"
        elif time(13, 0) <= now <= time(13, 15):
            return "afternoon_open"
        elif time(14, 50) <= now <= time(15, 5):
            return "afternoon_close"
    
    elif market in ["港股", "hk", "hongkong"]:
        if time(9, 30) <= now <= time(9, 45):
            return "morning_open"
        elif time(11, 55) <= now <= time(12, 10):
            return "morning_close"
        elif time(13, 0) <= now <= time(13, 15):
            return "afternoon_open"
        elif time(15, 50) <= now <= time(16, 5):
            return "afternoon_close"
    
    elif market in ["美股", "us", "usa"]:
        # 美股时段 (北京时间)
        if time(21, 30) <= now <= time(21, 45):
            return "market_open"
        elif time(3, 50) <= now <= time(4, 5):
            return "market_close"
    
    return ""

# ========== 消息发送 ==========
def send_alert(stock_name: str, title: str, content: str, channels: list, targets: dict):
    """发送提醒消息"""
    messages_sent = 0
    
    for channel in channels:
        message = f"**{title}**\n\n{content}"
        
        # 飞书需要@用户
        if channel == "feishu" and targets.get("feishu_user"):
            message = f'<at user_id="{targets["feishu_user"]}">用户</at>\n\n{message}'
        
        target = targets.get(channel, targets.get("default", ""))
        if not target:
            continue
        
        env = os.environ.copy()
        env['PATH'] = '/root/.nvm/current/bin:/root/.local/share/pnpm:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
        
        try:
            result = subprocess.run([
                '/root/.local/share/pnpm/openclaw', 'message', 'send',
                '--channel', channel,
                '--target', target,
                '--message', message
            ], capture_output=True, text=True, timeout=30, env=env)
            
            if result.returncode == 0:
                log(f"✅ {channel} 消息已发送: {title}")
                messages_sent += 1
            else:
                log(f"❌ {channel} 发送失败: {result.stderr}")
        except Exception as e:
            log(f"❌ {channel} 发送异常: {e}")
    
    return messages_sent > 0

# ========== 主逻辑 ==========
def check_and_alert():
    """检查所有监控股票并发送提醒"""
    config = safe_read_json(CONFIG_FILE, {"stocks": [], "channels": [], "targets": {}})
    
    if not config.get("stocks"):
        log("没有配置监控股票")
        return
    
    data = safe_read_json(DATA_FILE, {"history": {}, "sent_today": {}})
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 确保数据结构
    if "history" not in data:
        data["history"] = {}
    if "sent_today" not in data:
        data["sent_today"] = {}
    if today not in data["history"]:
        data["history"][today] = {}
    
    for stock in config["stocks"]:
        market = stock.get("market", "A股")
        code = stock.get("code", "")
        name = stock.get("name", code)
        alert_prices = stock.get("alert_prices", {})  # {"up": 50.0, "down": 40.0}
        
        if not code:
            continue
        
        # 检查是否在交易时段
        if not is_trading_time(market):
            continue
        
        # 获取行情
        quote = get_quote(market, code)
        if not quote or not quote.get("valid"):
            log(f"{name} ({market}) 行情无效或获取失败")
            continue
        
        log(f"行情: {quote['name']} ({market}) {quote['current']:.2f}")
        
        stock_key = f"{market}_{code}"
        if stock_key not in data["history"][today]:
            data["history"][today][stock_key] = {}
        
        stock_data = data["history"][today][stock_key]
        slot = get_time_slot(market)
        sent_key = f"{stock_key}_{today}"
        
        # 开盘/收盘提醒
        if slot and f"{sent_key}_{slot}" not in data["sent_today"]:
            change_pct = (quote["current"] - quote["prev_close"]) / quote["prev_close"] * 100
            direction = "📈" if change_pct >= 0 else "📉"
            now_str = datetime.now().strftime("%H:%M:%S")
            
            slot_names = {
                "morning_open": "🌅 早盘开盘",
                "morning_close": "🍽️ 上午收盘",
                "afternoon_open": "☀️ 午盘开盘",
                "afternoon_close": "🌆 全天收盘",
                "market_open": "🌅 开盘",
                "market_close": "🌆 收盘"
            }
            
            if send_alert(
                name,
                f"{slot_names.get(slot, '📈')} {name} ({code})",
                f"⏰ 时间: {now_str}\n"
                f"💰 当前价格: {quote['current']:.2f} 元\n"
                f"📊 今日开盘: {quote['open']:.2f} 元\n"
                f"📅 昨日收盘: {quote['prev_close']:.2f} 元\n"
                f"⬆️ 今日最高: {quote['high']:.2f} 元\n"
                f"⬇️ 今日最低: {quote['low']:.2f} 元\n"
                f"📈 成交量: {quote['volume']/10000:.0f} 万手\n"
                f"{direction} 涨跌幅: {change_pct:+.2f}%",
                config.get("channels", ["feishu"]),
                config.get("targets", {})
            ):
                data["sent_today"][f"{sent_key}_{slot}"] = now_str
        
        # 价格异动检测
        last_price = stock_data.get("last_check_price", quote["current"])
        if last_price > 0:
            price_change_pct = (quote["current"] - last_price) / last_price * 100
            
            if abs(price_change_pct) >= PRICE_CHANGE_THRESHOLD:
                alert_key = f"{sent_key}_price_{datetime.now().strftime('%Y%m%d%H%M')}"
                
                if alert_key not in data["sent_today"]:
                    now_str = datetime.now().strftime("%H:%M:%S")
                    direction = "📈 急剧拉升" if price_change_pct > 0 else "📉 急剧下跌"
                    price_diff = quote["current"] - last_price
                    
                    if send_alert(
                        name,
                        f"⚠️ {name} ({code}) {direction}",
                        f"⏰ 时间: {now_str}\n"
                        f"💰 当前价格: {quote['current']:.2f} 元\n"
                        f"📊 上次价格: {last_price:.2f} 元\n"
                        f"📈 价格变动: {price_diff:+.2f} 元 ({price_change_pct:+.2f}%)\n"
                        f"📉 成交量: {quote['volume']/10000:.0f} 万手",
                        config.get("channels", ["feishu"]),
                        config.get("targets", {})
                    ):
                        data["sent_today"][alert_key] = now_str
        
        # 涨破/跌破价格提醒
        if alert_prices:
            up_price = alert_prices.get("up")
            down_price = alert_prices.get("down")
            now_str = datetime.now().strftime("%H:%M:%S")
            
            if up_price and quote["current"] >= up_price:
                alert_key = f"{sent_key}_up_{up_price}"
                if alert_key not in data["sent_today"]:
                    if send_alert(
                        name,
                        f"🎯 {name} ({code}) 涨破目标价",
                        f"⏰ 时间: {now_str}\n"
                        f"💰 当前价格: {quote['current']:.2f} 元\n"
                        f"🎯 目标价格: {up_price:.2f} 元\n"
                        f"✅ 已涨破目标价 {quote['current'] - up_price:+.2f} 元",
                        config.get("channels", ["feishu"]),
                        config.get("targets", {})
                    ):
                        data["sent_today"][alert_key] = now_str
            
            if down_price and quote["current"] <= down_price:
                alert_key = f"{sent_key}_down_{down_price}"
                if alert_key not in data["sent_today"]:
                    if send_alert(
                        name,
                        f"🎯 {name} ({code}) 跌破目标价",
                        f"⏰ 时间: {now_str}\n"
                        f"💰 当前价格: {quote['current']:.2f} 元\n"
                        f"🎯 目标价格: {down_price:.2f} 元\n"
                        f"⚠️ 已跌破目标价 {quote['current'] - down_price:.2f} 元",
                        config.get("channels", ["feishu"]),
                        config.get("targets", {})
                    ):
                        data["sent_today"][alert_key] = now_str
        
        # 更新数据
        stock_data["last_check_price"] = quote["current"]
        stock_data["last_check_time"] = quote["time"]
        stock_data.update({
            "name": quote["name"],
            "current": quote["current"],
            "high": quote["high"],
            "low": quote["low"],
            "volume": quote["volume"]
        })
    
    # 清理旧数据
    all_dates = sorted(data["history"].keys(), reverse=True)
    for old_date in all_dates[30:]:
        del data["history"][old_date]
    
    # 清理今日之前的提醒记录
    for key in list(data["sent_today"].keys()):
        if today not in key:
            del data["sent_today"][key]
    
    safe_write_json(DATA_FILE, data)

if __name__ == "__main__":
    check_and_alert()