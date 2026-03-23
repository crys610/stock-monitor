---
name: stock-monitor
description: 多市场股票盯盘技能。支持A股、港股、美股的实时监控和提醒。触发场景：(1) 用户要求监控某只股票；(2) 用户要求添加/删除股票监控；(3) 用户询问监控列表；(4) 用户设置涨破/跌破价格提醒。支持群聊交互，直接说"监控 XXX"即可。
---

# 股票盯盘技能

多市场股票实时监控，支持 A股、港股、美股。

## 快速开始

### 添加监控

用户说：
- "帮我监控北方稀土"
- "监控 A股 600111"
- "监控港股腾讯 00700"
- "监控美股苹果 AAPL"
- "监控北方稀土，涨破50提醒我，跌破40也提醒"

### 管理监控

- "查看我的监控列表"
- "删除北方稀土监控"
- "停止监控 600111"

## 脚本使用

### 添加股票

```bash
# A股
python scripts/config.py add A股 600111 北方稀土

# 带价格提醒
python scripts/config.py add A股 600111 北方稀土 50 40

# 港股
python scripts/config.py add 港股 00700 腾讯

# 美股
python scripts/config.py add 美股 AAPL 苹果
```

### 删除股票

```bash
python scripts/config.py remove A股 600111
```

### 查看列表

```bash
python scripts/config.py list
```

### 设置提醒目标

```bash
# 飞书群聊
python scripts/config.py target feishu oc_xxx

# 飞书用户 (用于@)
python scripts/config.py target feishu_user ou_xxx

# 微信
python scripts/config.py target wechat xxx
```

## 监控功能

### 时段提醒

| 市场 | 开盘 | 收盘 |
|------|------|------|
| A股 | 9:30 | 15:00 |
| 港股 | 9:30 | 16:00 |
| 美股 | 21:30 (北京时间) | 04:00 |

### 价格异动

- 单次涨跌超过阈值自动提醒
- 显示涨跌幅、成交量变化

### 自定义价格提醒

- 涨破某价格提醒
- 跌破某价格提醒

## 配置文件

`config.json` 结构：

```json
{
  "stocks": [
    {
      "market": "A股",
      "code": "600111",
      "name": "北方稀土",
      "alert_prices": {
        "up": 50.0,
        "down": 40.0
      }
    }
  ],
  "channels": ["feishu"],
  "targets": {
    "feishu": "oc_xxx",
    "feishu_user": "ou_xxx"
  },
  "price_change_threshold": 1.0
}
```

## 定时任务

建议 cron 配置：

```bash
# A股交易时段 (工作日 9:30-15:00)
*/5 9-11,13-15 * * 1-5 python /path/to/scripts/monitor.py

# 开盘检测 (每分钟)
* 9-10 * * 1-5 python /path/to/scripts/monitor.py

# 美股交易时段 (北京时间 21:30-04:00)
*/5 21-23 * * 0-4 python /path/to/scripts/monitor.py
*/5 0-4 * * 1-5 python /path/to/scripts/monitor.py
```

## 数据来源

| 市场 | 数据源 |
|------|--------|
| A股 | 新浪财经 |
| 港股 | 腾讯财经 |
| 美股 | Yahoo Finance |

## 注意事项

- A股/港股数据有15分钟延迟
- 美股数据为实时数据
- 非交易时段自动跳过检测