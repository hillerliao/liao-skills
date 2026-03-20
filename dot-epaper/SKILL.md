---
name: dot-epaper
description: Push text and poetry to Dot e-ink devices via direct API. Use when user wants to send text, poetry, or notifications to Dot e-ink display devices.
---

# Dot E-ink Display Push

Push text, poetry, and notifications to Dot e-ink devices via direct API.

## Quick Start

```bash
# Configure your device mapping first
cp config/device-map.txt.example config/device-map.txt
# Edit config/device-map.txt with your device IDs

# Set API key in environment
export DOT_API_KEY=your_api_key_here

# Push to device
./scripts/dot-send.sh <device> <title> <message> [signature]

# Examples
./scripts/dot-send.sh toilet "村居" "草长莺飞二月天..." "清·高鼎"
./scripts/dot-send.sh fridge "江南春" "千里莺啼绿映红..." "唐代·杜牧"
./scripts/dot-send.sh all "标题" "内容" "作者"
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
living_room:YOUR_DEVICE_ID
bedroom:YOUR_DEVICE_ID
```

## API Limits

- Title: max 10 characters
- Message: max 40 characters
- Signature: max 10 characters

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.
