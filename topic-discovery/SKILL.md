---
name: topic-discovery
description: Discover potential article topics from conversation history. Use when user asks: review conversations, find topics, 公众号选题, article ideas, what did we discuss today, identify topics from chat history. Triggers on phrases like: "今天聊了什么", "review conversations", "find topics", "公众号选题", "identify article ideas", "topic discovery", "what did we discuss".
---

# Topic Discovery

Discover article topics from conversation history across all channels for WeChat/公众号 content creation.

## Quick Start

```bash
# Run the script
python3 scripts/discover_topics.py 1440   # last 24 hours
python3 scripts/discover_topics.py 2880   # last 48 hours
```

## Output

The script generates a report with:
- 26 specific topics detected
- 9 broad categories
- Relevance scores (1-5 stars)
- 3 article angle suggestions per topic

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Time range | 1440 (24h) | Minutes to analyze |

## How It Works

1. Extracts all text from session files (`~/.openclaw/agents/main/sessions/`)
2. Matches against 200+ keywords across 10 categories
3. Scores topics by mention frequency
4. Generates article angle suggestions

## Best Practices

- Create memory files for every session to avoid missed topics
- Run daily to track evolving interests
- Focus on high-score topics for article content

## See Also

- `references/article-templates.md` - Article angle templates
