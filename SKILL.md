# Dot E-ink Display Push

Push text and poetry to Dot e-ink devices via direct API.

## Features

- 📱 Push to multiple Dot devices (toilet, fridge, etc.)
- 📜 Support for poetry and text messages
- 🔄 Push to all devices at once
- 📝 Logging of push history
- ⏱️ Timeout protection
- 🔒 Credentials loaded from environment

## Installation

```bash
clawhub install dot-epaper
```

## Configuration

Set these in your `.env`:

```bash
# Dot API credentials
DOT_API_KEY=your_api_key_here
DOT_DEVICE_ID=your_default_device_id
```

Device mapping is configured in `config/device-map.txt`:
```
toilet:48F6EE576924
fridge:B43A455B9660
```

## Usage

```bash
# Push to specific device
dot-send toilet "村居" "草长莺飞二月天..." "清·高鼎"
dot-send fridge "江南春" "千里莺啼..." "唐代·杜牧"

# Push to all devices
dot-send all "标题" "内容" "作者"

# Show help
dot-send help
```

## Available Commands

| Command | Description |
|---------|-------------|
| `toilet` | Push to toilet device |
| `fridge` | Push to fridge device |
| `all` | Push to all devices |
| `help` | Show usage |

## Requirements

- Dot e-ink device with Text API enabled
- API key from Dot app
- curl command

## License

MIT
