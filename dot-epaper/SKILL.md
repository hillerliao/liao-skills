---
name: dot-epaper
description: Push any text content to Dot e-ink devices via direct API. Use when user wants to send text, notes, labels, status, or any static content to Dot e-ink display devices.
---

# Dot E-ink Display Push

Push any text content to Dot e-ink devices via direct API.

## Use Cases

- 📜 **诗词** - 每天一首诗，冰箱上的诗意
- 💬 **便签** - 留言提醒，"下班记得接孩子"
- 🏷️ **标签** - 冰箱物品记录，"鸡蛋：3个"
- 📝 **状态** - 办公状态，"工作中请勿打扰"
- 💡 **语录** - 每日一言、励志句子
- 📢 **公告** - 家庭/团队通知
- 🎯 **目标** - 每日目标展示

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
# Push poetry (诗词)
./scripts/dot-send.sh fridge "江南春" "千里莺啼绿映红，水村山郭酒旗风。南朝四百八十寺，多少楼台烟雨中。" "唐代·杜牧"

# Leave a note (便签)
./scripts/dot-send.sh toilet "提醒" "下班记得接孩子" ""

# Fridge inventory (冰箱库存)
./scripts/dot-send.sh fridge "库存" "鸡蛋：3个，牛奶：1盒" ""

# Working status (办公状态)
./scripts/dot-send.sh bedroom "状态" "工作中，请勿打扰" ""

# Daily quote (每日一言)
./scripts/dot-send.sh bedroom "一言" "今天也要加油呀" ""

# Family announcement (家庭公告)
./scripts/dot-send.sh fridge "通知" "今晚8点家庭会议" ""

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

## Note

This skill pushes static text content to the device. It does not include timing, notifications, or alerts. The content remains displayed until you push new content.

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.
