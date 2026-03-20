# Dot E-ink Display Push

Push text, poetry, and notifications to Dot e-ink devices via direct API.

## Features

- 📱 Push to multiple Dot devices (living room, bedroom, kitchen, etc.)
- 📜 Support for poetry and text messages
- 🔄 Push to all devices at once
- 📝 Logging of push history
- ⏱️ Timeout protection
- 🔒 Credentials loaded from environment
- 🎯 Configurable device aliases

## Installation

```bash
# Clone the repository
git clone https://github.com/hillerliao/dot-epaper-skill.git
cd dot-epaper-skill

# Or install via ClawHub
clawhub install dot-epaper
```

## Configuration

### 1. Get Dot API Credentials

1. Open Dot app on your phone
2. Go to Device Settings → API
3. Enable "Text API" content type
4. Copy your API Key and Device ID

### 2. Set Environment Variables

Create or edit `~/.openclaw/.env`:

```bash
# Dot API credentials
DOT_API_KEY=your_api_key_here
```

### 3. Configure Device Mapping

Edit `config/device-map.txt`:

```
# Format: <alias>:<device_id>
living_room:YOUR_DEVICE_ID_1
bedroom:YOUR_DEVICE_ID_2
kitchen:YOUR_DEVICE_ID_3
```

## Usage

```bash
# Push to specific device
./scripts/dot-send.sh living_room "村居" "草长莺飞二月天..." "清·高鼎"
./scripts/dot-send.sh bedroom "江南春" "千里莺啼绿映红..." "唐代·杜牧"

# Push to all devices
./scripts/dot-send.sh all "标题" "内容" "作者"

# Show help
./scripts/dot-send.sh help
```

## Requirements

- Dot e-ink device with Text API enabled
- API key from Dot app
- curl command
- bash 4.0+

## API Limits

- Title: max 10 characters (Chinese display length)
- Message: max 40 characters (Chinese display length)
- Signature: max 10 characters

## Troubleshooting

### "curl: command not found"

Install curl:
```bash
# macOS
brew install curl

# Ubuntu/Debian
sudo apt install curl

# CentOS/RHEL
sudo yum install curl
```

### "DOT_API_KEY not set"

Make sure your `.env` file is configured:
```bash
# Check if file exists
cat ~/.openclaw/.env

# Or set temporarily for testing
export DOT_API_KEY=your_key_here
```

### "No devices configured"

Edit `config/device-map.txt` to add your devices:
```
living_room:YOUR_DEVICE_ID
```

### "Title too long" / "Message too long"

Check the API limits and shorten your content:
- Title: max 10 characters
- Message: max 40 characters
- Signature: max 10 characters

### "Failed to connect to API"

Check your network connection:
```bash
# Test API connectivity
curl -I https://dot.mindreset.tech
```

### "Unknown device 'xxx'"

Verify your device alias exists in `config/device-map.txt`:
```bash
# Show configured devices
./scripts/dot-send.sh help
```

### Device shows "offline" or "sleeping"

This is normal when the device is in sleep mode. The content will be displayed on the next wake cycle.

## FAQ

**Q: Can I use special characters like emoji?**
A: Yes, but they count toward the character limit. Emoji may display differently on the e-ink screen.

**Q: How do I find my device ID?**
A: In the Dot app, go to Device Settings → API → Device ID

**Q: Can I push to multiple devices at once?**
A: Yes, use `all` as the device name: `./dot-send.sh all "title" "message"`

**Q: Where are the logs?**
A: Logs are stored in `logs/push.log`

## License

MIT License - see LICENSE file

## Contributing

PRs welcome! Please ensure:
- Code follows existing style
- Tests pass
- Documentation is updated

## Acknowledgments

- [mindreset-dot-mcp](https://github.com/lakphy/mindreset-dot-mcp) - Original MCP server
- [Dot](https://dot.mindreset.tech/) - E-ink device platform
