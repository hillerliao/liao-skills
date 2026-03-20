# Troubleshooting

## "curl: command not found"

Install curl:
```bash
# macOS
brew install curl

# Ubuntu/Debian
sudo apt install curl

# CentOS/RHEL
sudo yum install curl
```

## "DOT_API_KEY not set"

Set the environment variable:
```bash
export DOT_API_KEY=your_api_key_here
```

Or add to `~/.openclaw/.env`:
```
DOT_API_KEY=your_api_key_here
```

## "No devices configured"

Copy the example config:
```bash
cp config/device-map.txt.example config/device-map.txt
```

Then edit with your device IDs.

## "Unknown device 'xxx'"

Verify your device alias exists in `config/device-map.txt`:
```bash
./scripts/dot-send.sh help
```

## "Title too long" / "Message too long"

Shorten your content to fit API limits:
- Title: max 10 characters
- Message: max 40 characters
- Signature: max 10 characters

## "Failed to connect to API"

Test network connectivity:
```bash
curl -I https://dot.mindreset.tech
```

## Device shows "offline" or "sleeping"

Normal when device is in sleep mode. Content will display on next wake cycle.
