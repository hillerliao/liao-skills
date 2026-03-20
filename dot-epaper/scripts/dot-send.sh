#!/bin/bash
# Dot E-ink device push script
# Part of dot-epaper skill

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"
DEVICE_MAP_FILE="${CONFIG_DIR}/config/device-map.txt"
LOG_FILE="${CONFIG_DIR}/logs/push.log"

# Default device map - EMPTY for security, users must configure their own
DEFAULT_DEVICE_MAP=""

# API endpoint
API_URL="https://dot.mindreset.tech/api/authV2/open/device"

# API limits
MAX_TITLE_LEN=10
MAX_MESSAGE_LEN=40
MAX_SIGNATURE_LEN=10

# Retry settings
MAX_RETRIES=3
RETRY_DELAY=2

# Load credentials
if [ -f "$HOME/.openclaw/.env" ]; then
    source "$HOME/.openclaw/.env"
fi

# Check dependencies
command -v curl >/dev/null 2>&1 || { echo "Error: curl is required but not installed."; exit 1; }

# Escape special characters for JSON
json_escape() {
    local str="$1"
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/\\n}"
    str="${str//$'\r'/}"
    str="${str//$'\t'/\\t}"
    echo "$str"
}

# Validate length
validate_length() {
    local name="$1"
    local value="$2"
    local max="$3"
    
    local len=$(echo -n "$value" | wc -m)
    if [ "$len" -gt "$max" ]; then
        echo "Error: $name too long ($len > $max chars): '$value'"
        return 1
    fi
    return 0
}

# Logging
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

# Show help
show_help() {
    cat <<EOF
Dot E-ink Device Push

Usage:
    dot-send <device> <title> <message> [signature]
    dot-send help

Devices:
EOF
    if [ -f "$DEVICE_MAP_FILE" ]; then
        grep -v "^#" "$DEVICE_MAP_FILE" | grep -v "^$" | while read -r line; do
            echo "    - $(echo "$line" | cut -d: -f1)"
        done
    fi
    if [ -n "$DEFAULT_DEVICE_MAP" ]; then
        echo "$DEFAULT_DEVICE_MAP" | while read -r line; do
            echo "    - $(echo "$line" | cut -d: -f1)"
        done
    fi
    if [ ! -f "$DEVICE_MAP_FILE" ] && [ -z "$DEFAULT_DEVICE_MAP" ]; then
        echo "    (none - please configure config/device-map.txt)"
    fi
    cat <<EOF

API Limits:
    Title: max $MAX_TITLE_LEN characters
    Message: max $MAX_MESSAGE_LEN characters  
    Signature: max $MAX_SIGNATURE_LEN characters

Examples:
    dot-send toilet "村居" "草长莺飞二月天..." "清·高鼎"
    dot-send fridge "江南春" "千里莺啼绿映红..." "唐代·杜牧"
    dot-send all "标题" "内容" "作者"
EOF
}

# Get device map
get_device_map() {
    if [ -f "$DEVICE_MAP_FILE" ]; then
        grep -v "^#" "$DEVICE_MAP_FILE" | grep -v "^$"
    elif [ -n "$DEFAULT_DEVICE_MAP" ]; then
        echo "$DEFAULT_DEVICE_MAP"
    fi
}

# Send to single device with retry
send_to_device() {
    local device_id="$1"
    local title="$2"
    local message="$3"
    local signature="${4:-}"

    if [ -z "$DOT_API_KEY" ]; then
        echo "Error: DOT_API_KEY not set"
        return 1
    fi

    title=$(json_escape "$title")
    message=$(json_escape "$message")
    signature=$(json_escape "$signature")

    validate_length "Title" "$title" "$MAX_TITLE_LEN" || return 1
    validate_length "Message" "$message" "$MAX_MESSAGE_LEN" || return 1
    if [ -n "$signature" ]; then
        validate_length "Signature" "$signature" "$MAX_SIGNATURE_LEN" || return 1
    fi

    local payload="{\"refreshNow\": true, \"title\": \"$title\", \"message\": \"$message\""
    if [ -n "$signature" ]; then
        payload="$payload, \"signature\": \"$signature\""
    fi
    payload="$payload}"

    local attempt=1
    while [ "$attempt" -le "$MAX_RETRIES" ]; do
        local response
        response=$(curl -s --max-time 10 \
            -X POST "$API_URL/$device_id/text" \
            -H "Authorization: Bearer $DOT_API_KEY" \
            -H "Content-Type: application/json" \
            -d "$payload" 2>&1) || {
            if [ "$attempt" -lt "$MAX_RETRIES" ]; then
                echo "Attempt $attempt failed, retrying in ${RETRY_DELAY}s..."
                sleep "$RETRY_DELAY"
                attempt=$((attempt + 1))
                continue
            else
                echo "Error: Failed after $MAX_RETRIES attempts"
                return 1
            fi
        }

        if echo "$response" | grep -q "error"; then
            echo "API Error: $response"
            return 1
        fi

        echo "$response"
        return 0
    done
}

# Main
main() {
    if [ $# -lt 1 ] || [ "$1" = "help" ]; then
        show_help
        exit 0
    fi

    local device_name="$1"
    local title="${2:-}"
    local message="${3:-}"
    local signature="${4:-}"

    if [ -z "$title" ] || [ -z "$message" ]; then
        echo "Error: Title and message required"
        show_help
        exit 1
    fi

    local device_map
    device_map=$(get_device_map)

    if [ -z "$device_map" ]; then
        echo "Error: No devices configured. Please set up config/device-map.txt"
        exit 1
    fi

    if [ "$device_name" = "all" ]; then
        log "Push to ALL devices: $title"
        while IFS=: read -r name id; do
            echo -n "→ $name: "
            send_to_device "$id" "$title" "$message" "$signature"
        done <<< "$device_map"
    else
        local device_id
        device_id=$(echo "$device_map" | grep "^${device_name}:" | cut -d: -f2)

        if [ -z "$device_id" ]; then
            echo "Error: Unknown device '$device_name'"
            show_help
            exit 1
        fi

        log "Push to $device_name ($device_id): $title"
        send_to_device "$device_id" "$title" "$message" "$signature"
    fi
}

main "$@"
