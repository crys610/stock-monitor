# Stock Monitor 📈

多市场股票盯盘技能，支持 A股、港股、美股的实时监控和提醒。

## 功能特性

- 🌍 **多市场支持**: A股、港股、美股
- ⏰ **时段提醒**: 开盘/收盘自动提醒
- 📊 **价格异动**: 单次涨跌超过阈值自动提醒
- 🎯 **目标价格**: 涨破/跌破目标价提醒
- 📱 **多渠道通知**: 飞书、微信等

## 快速开始

### 安装依赖

```bash
pip install requests
```

### 配置

复制配置模板：

```bash
cp examples/config.example.json config.json
```

编辑 `config.json`：

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
    "feishu": "your_chat_id",
    "feishu_user": "your_user_id"
  },
  "price_change_threshold": 1.0
}
```

### 运行

```bash
python scripts/monitor.py
```

### 定时任务

添加到 crontab：

```bash
# A股交易时段 (工作日 9:25-15:05)
*/5 9-11,13-15 * * 1-5 python /path/to/scripts/monitor.py
* 9-10 * * 1-5 python /path/to/scripts/monitor.py

# 美股交易时段 (北京时间 21:25-04:05)
*/5 21-23 * * 0-4 python /path/to/scripts/monitor.py
*/5 0-4 * * 1-5 python /path/to/scripts/monitor.py
```

## 配置管理

```bash
# 添加股票
python scripts/config.py add A股 600111 北方稀土

# 带价格提醒
python scripts/config.py add A股 600111 北方稀土 50 40

# 港股
python scripts/config.py add 港股 00700 腾讯

# 美股
python scripts/config.py add 美股 AAPL 苹果

# 删除股票
python scripts/config.py remove A股 600111

# 查看列表
python scripts/config.py list

# 设置提醒目标
python scripts/config.py target feishu your_chat_id
```

## 提醒类型

| 类型 | 说明 |
|------|------|
| 🌅 早盘开盘 | 9:30-9:45 |
| 🍽️ 上午收盘 | 11:25-11:35 |
| ☀️ 午盘开盘 | 13:00-13:15 |
| 🌆 全天收盘 | 14:50-15:05 |
| ⚠️ 价格异动 | 单次涨跌超过阈值 |
| 🎯 目标价格 | 涨破/跌破设定价格 |

## 数据来源

| 市场 | 数据源 | 延迟 |
|------|--------|------|
| A股 | 新浪财经 | ~15秒 |
| 港股 | 腾讯财经 | ~15秒 |
| 美股 | Yahoo Finance | 实时 |

## OpenClaw 集成

本技能为 [OpenClaw](https://github.com/openclaw/openclaw) 技能，可配合 OpenClaw CLI 使用：

```bash
# 安装技能
openclaw skill install stock-monitor.skill
```

## License

Apache 2.0 License