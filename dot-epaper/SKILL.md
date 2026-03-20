---
name: dot-epaper
description: Push any text content to Dot e-ink devices via direct API. Use when user wants to send text, poetry, weather, reminders, notifications, or any content to Dot e-ink display devices.
---

# Dot E-ink Display Push

Push any text content to Dot e-ink devices via direct API.

## Use Cases

- 📜 **古诗词** - 冰箱贴、卫生间显示诗词
- 🌤️ **天气** - 今日天气、明日预报
- ✅ **待办** - 今日待办事项
- 📦 **快递** - 物流状态提醒
- 📊 **股票** - 行情提醒
- ⏰ **提醒** - 会议、午睡、服药提醒
- 💬 **便签** - 留言板功能
- 📰 **摘要** - 新闻、文章摘要

## Quick Start

```bash
# Configure your device mapping first
cp config/device-map.txt.example config/device-map.txt
# Edit config/device-map.txt with your device IDs

# Set API key in environment
export DOT_API_KEY=your_api_key_here

# Push to device
./scripts/dot-send.sh <device> <title> <message> [signature]
```

## Examples

```bash
# Push poetry
./scripts/dot-send.sh fridge "江南春" "千里莺啼绿映红，水村山郭酒旗风。南朝四百八十寺，多少楼台烟雨中。" "唐代·杜牧"

# Push weather
./scripts/dot-send.sh bedroom "今日天气" "晴 20-28°C" ""

# Push reminder
./scripts/dot-send.sh toilet "会议提醒" "14:00 周会" ""

# Push package status
./scripts/dot-send.sh fridge "快递" "已到驿站" ""

# Push to all devices
./scripts/dot-send.sh all "标题" "内容" ""
```

## Configuration

### 1. Get API Credentials

1. Open Dot app → Device Settings → API
2. Enable "Text API" content type
3. Copy API Key and Device ID

### 2. Set Environment Variable

```bash
export DOT_API_KEY=your_api_key_here
```

Or add to `~/.openclaw/.env`:
```
DOT_API_KEY=your_api_key_here
```

### 3. Configure Devices

Copy and edit `config/device-map.txt.example`:
```
# Format: <alias>:<device_id>
fridge:YOUR_FRIDGE_DEVICE_ID
toilet:YOUR_TOILET_DEVICE_ID
bedroom:YOUR_BEDROOM_DEVICE_ID
```

## API Limits

- Title: max 10 characters
- Message: max 40 characters
- Signature: max 10 characters

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.
