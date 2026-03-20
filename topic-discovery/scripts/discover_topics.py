#!/usr/bin/env python3
"""
Topic Discovery Script v3.0
AI-powered article topic discovery from conversation history.
Detects 26 specific topics and 9 broad categories.
"""

import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"

# ========== TOPIC KEYWORDS ==========
TOPIC_KEYWORDS = {
    'investment': [
        '投资', '基金', '股票', '港股', '美股', '雪球', '投顾', '理财', '资产',
        'A股', '理财', '收益', '华泰', '期货', '券商', '净值', '持仓', '分红',
        'portfolio', 'fund', 'stock', 'ETF', 'QDII', 'investment', 'trading',
        'broker', 'huatai', 'futures', 'mastercard', 'dividend'
    ],
    'tech-ai': [
        'ai', 'claude', 'gpt', '模型', 'model', 'chatgpt', 'openai', 'llm',
        'openclaw', 'github', 'mcp', 'server', '部署', '安装', 'terminal',
        'linux', 'windows', 'mac', 'android', 'termux', 'docker', '编程', '代码',
        '脚本', 'npm', 'python', 'javascript', 'rust', 'api', '接口', '认证',
        'token', '密钥', '登录', 'oauth', 'sse', 'websocket',
        'api key', 'model switching', 'minimax', 'mimo', 'opus', 'kimi'
    ],
    'dot-device': [
        '墨水屏', 'dot', '电子纸', 'mindreset', '派大星', '提醒', '推送通知',
        'e-ink', 'eink', 'dot device', 'ink display'
    ],
    'mcp-servers': [
        'mcp', '服务器', '工具', 'stargate', '金融数据', '基金数据', '组合',
        'mcp server', 'stargate', 'financial data', 'fund api'
    ],
    'parenting': [
        '育儿', '宝宝', '孩子', '教育', '小学', '入学', '学校', ' parenting',
        'kids', '深圳', '南山', '福田', '积分', '学位', '早教', '幼儿园',
        '兴趣班', '辅导班', '学区房', '租房', '民办', '公立', '国际学校',
        'Summerhill', '华德福', '蒙特梭利', '在家教育', 'homeschool',
        'parenting', 'education', 'school', 'admission'
    ],
    'news': [
        '新闻', 'news', '北京', '长汀', '中关村', '论坛', '医药', '健康',
        '科技', '创新', '创业', '公司', '政策', '政府', '国际', '美国',
        '伊朗', '以色列', '特朗普', '股市', '经济',
        'beijing', 'tech', 'innovation', 'politics', 'trump'
    ],
    'tools': [
        'searxng', '搜索', '笔记', 'obsidian', 'notion', 'quick notes', 'joplin',
        'automation', 'workflow', '自动化', '工作流', 'n8n', 'zapier', 'ifttt',
        'git', '版本控制', '同步', '备份', '云端', '坚果云', 'icloud', 'dropbox',
        'searxng', 'search', 'notes', 'automation', 'workflow',
        'git sync', 'cloud sync', 'backup'
    ],
    'data': [
        '数据', '分析', '爬虫', 'scrape', 'chart', '图表', 'pdf', 'api',
        '爬取', '抓取', '分析', '报告', '可视化', 'dashboard', '数据源',
        '小红书', '抖音', '微博', '知乎', 'b站', 'bilibili',
        'data', 'analysis', 'scrape', 'crawl', 'chart', 'visualization', 'pdf'
    ],
    'devops': [
        '服务器', 'vps', '域名', 'ssl', 'https', 'nginx', 'docker', 'k8s',
        'kubernetes', 'cloudflare', 'vercel', 'netlify', 'aws', '阿里云', '腾讯云',
        'server', 'vps', 'domain', 'ssl', 'nginx', 'docker', 'cloud', 'aws'
    ],
}

# ========== SPECIFIC TOPICS ==========
SPECIFIC_TOPICS = {
    'OpenClaw': {
        'keywords': ['OpenClaw', 'openclaw', 'ClawdBot'],
        'angles': ['《OpenClaw 安装与配置指南》', '《在 Termux 上运行 OpenClaw》', '《OpenClaw 高级功能教程》']
    },
    'ClawX': {
        'keywords': ['ClawX', 'clawx'],
        'angles': ['《ClawX 新版本体验报告》', '《ClawX vs OpenClaw 对比》', '《ClawX 安装指南》']
    },
    'GitHub Issues': {
        'keywords': ['GitHub', 'github issue', 'issue'],
        'angles': ['《开源项目 Issue 管理经验》', '《如何参与开源项目》', '《GitHub 维护技巧》']
    },
    'Termux': {
        'keywords': ['Termux', 'termux'],
        'angles': ['《Termux 入门指南》', '《在 Android 上运行 Python 环境》', '《Termux 高级用法》']
    },
    'MCP Server': {
        'keywords': ['MCP', 'mcp server', 'mcp'],
        'angles': ['《MCP 服务器实战》', '《AI 工具连接现实世界》', '《MCP 生态介绍》']
    },
    'SearXNG': {
        'keywords': ['SearXNG', 'searxng'],
        'angles': ['《自建隐私搜索引擎》', '《SearXNG 部署教程》', '《隐私搜索方案对比》']
    },
    'Model Switching': {
        'keywords': ['/model', '模型切换', 'model switching'],
        'angles': ['《AI 模型选择指南》', '《如何切换 AI 模型》', '《主流 AI 模型对比》']
    },
    '雪球投顾': {
        'keywords': ['雪球', '投顾'],
        'angles': ['《雪球投顾组合分析》', '《智能投顾对比》', '《基金投顾怎么选》']
    },
    '基金': {
        'keywords': ['基金', 'fund'],
        'angles': ['《基金入门教程》', '《基金配置策略》', '《如何挑选基金》']
    },
    '股票': {
        'keywords': ['股票', 'stock'],
        'angles': ['《股票投资基础》', '《港股/美股开户》', '《股票分析技巧》']
    },
    '港股': {
        'keywords': ['港股'],
        'angles': ['《港股开户指南》', '《港股ETF推荐》', '《港股打新攻略》']
    },
    '美股': {
        'keywords': ['美股'],
        'angles': ['《美股开户指南》', '《如何买美股》', '《美股ETF推荐》']
    },
    'Mastercard': {
        'keywords': ['Mastercard'],
        'angles': ['《Mastercard 股价分析》', '《信用卡投资》', '《支付股票研究》']
    },
    '华泰期货': {
        'keywords': ['华泰', '期货'],
        'angles': ['《华泰期货开户》', '《期货入门教程》', '《期货交易策略》']
    },
    '育儿笔记': {
        'keywords': ['育儿笔记'],
        'angles': ['《育儿笔记方案》', '《宝宝成长记录》', '《育儿工具推荐》']
    },
    '小学入学': {
        'keywords': ['小学', '入学', '学位'],
        'angles': ['《深圳小学入学攻略》', '《积分入学指南》', '《学区房 vs 租房》']
    },
    '深圳教育': {
        'keywords': ['深圳', '南山', '福田'],
        'angles': ['《深圳教育规划》', '《南山 vs 福田》', '《深圳学校选择》']
    },
    '北京新闻': {
        'keywords': ['北京新闻', 'beijing'],
        'angles': ['《北京新闻解读》', '《北京科技动态》', '《北京政策分析》']
    },
    '长汀新闻': {
        'keywords': ['长汀'],
        'angles': ['《长汀新闻汇总》', '《长汀发展动态》', '《长汀特色产业》']
    },
    '中关村论坛': {
        'keywords': ['中关村', '论坛'],
        'angles': ['《中关村论坛解读》', '《北京科技论坛》', '《科技创新趋势》']
    },
    '笔记同步': {
        'keywords': ['笔记同步', '云端', '同步'],
        'angles': ['《笔记同步方案》', '《云端笔记推荐》', '《Obsidian 同步》']
    },
    'Obsidian': {
        'keywords': ['Obsidian', 'obsidian'],
        'angles': ['《Obsidian 入门》', '《Obsidian 插件推荐》', '《双向链接笔记法》']
    },
    '公众号': {
        'keywords': ['公众号', 'WeChat', '微信'],
        'angles': ['《公众号运营》', '《公众号选题技巧》', '《公众号增长策略》']
    },
    '文章选题': {
        'keywords': ['选题', '文章'],
        'angles': ['《选题方法论》', '《内容创作灵感》', '《爆款文章分析》']
    },
    'Dot墨水屏': {
        'keywords': ['Dot', '墨水屏', 'e-ink', 'eink'],
        'angles': ['《Dot 墨水屏体验》', '《电子纸设备推荐》', '《墨水屏应用场景》']
    },
    'stargate': {
        'keywords': ['stargate'],
        'angles': ['《stargate 金融数据》', '《MCP 金融工具》', '《AI 投资助手》']
    },
}

# ========== FUNCTIONS ==========
def get_recent_sessions(minutes: int = 1440):
    sessions = []
    cutoff = datetime.now() - timedelta(minutes=minutes)
    for f in SESSIONS_DIR.glob("*.jsonl"):
        if ".lock" in f.name:
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime > cutoff:
            sessions.append(f)
    return sorted(sessions, key=lambda x: x.stat().st_mtime, reverse=True)


def extract_all_text_content(session_file: Path):
    content_items = []
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get('type') == 'message':
                        msg = obj.get('message', {})
                        role = msg.get('role')
                        content = msg.get('content', [])
                        for c in content:
                            if c.get('type') == 'text':
                                text = c.get('text', '')
                                if text:
                                    content_items.append({'text': text, 'role': role, 'source': 'message'})
                    if obj.get('type') == 'toolResult':
                        content = obj.get('content', [])
                        for c in content:
                            if isinstance(c, dict) and c.get('type') == 'text':
                                text = c.get('text', '')
                                if text and len(text) > 20:
                                    content_items.append({'text': text[:500], 'role': 'tool', 'source': 'toolResult'})
                except:
                    continue
    except Exception as e:
        print(f"Error reading {session_file}: {e}", file=sys.stderr)
    return content_items


def extract_topics_from_full_text(content_items: list, topic_keywords: dict):
    topic_matches = defaultdict(list)
    for item in content_items:
        text = item.get('text', '')
        role = item.get('role', '')
        for topic, keywords in topic_keywords.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    topic_matches[topic].append({'text': text[:150], 'role': role, 'source': item.get('source', '')})
                    break
    return topic_matches


def extract_specific_topics(content_items: list, specific_topics: dict):
    topic_matches = defaultdict(list)
    for item in content_items:
        text = item.get('text', '')
        for topic_name, topic_data in specific_topics.items():
            keywords = topic_data.get('keywords', [])
            for kw in keywords:
                if kw.lower() in text.lower():
                    topic_matches[topic_name].append({'text': text[:150], 'role': item.get('role', ''), 'source': item.get('source', '')})
                    break
    return topic_matches


def calculate_specific_score(matches: list):
    if not matches:
        return 0
    count = len(matches)
    if count >= 100:
        return 5
    elif count >= 50:
        return 4
    elif count >= 20:
        return 3
    elif count >= 10:
        return 2
    else:
        return 1


def calculate_full_text_score(matches: list):
    if not matches:
        return 0
    unique_texts = len(set(m.get('text', '')[:50] for m in matches))
    roles = set(m.get('role', '') for m in matches)
    sources = set(m.get('source', '') for m in matches)
    score = min(5, max(1, min(5, unique_texts // 2) + min(2, len(roles)) + min(1, len(sources))))
    return score


def get_memory_files(days: int = 2):
    memories = []
    today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=i)
        pattern = f"*{date.strftime('%Y-%m-%d')}*.md"
        for f in MEMORY_DIR.glob(pattern):
            if f.name != 'MEMORY.md' and 'MEMORY.md' not in f.name:
                try:
                    content = f.read_text(encoding='utf-8')
                    memories.append({'file': f.name, 'content': content, 'mtime': datetime.fromtimestamp(f.stat().st_mtime)})
                except:
                    pass
    return memories


def parse_memory_topics(memories: list):
    memory_topics = defaultdict(lambda: {'files': set(), 'content': [], 'scores': 0})
    for mem in memories:
        content = mem['content']
        filename = mem['file']
        for topic, keywords in TOPIC_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw.lower() in content.lower())
            if count > 0:
                memory_topics[topic]['files'].add(filename)
                memory_topics[topic]['scores'] += count
    for topic in memory_topics:
        memory_topics[topic]['files'] = list(memory_topics[topic]['files'])
    return memory_topics


def generate_report(minutes: int = 1440):
    sessions = get_recent_sessions(minutes)
    memory_files = get_memory_files(2)
    
    all_content = []
    for session in sessions:
        content_items = extract_all_text_content(session)
        all_content.extend(content_items)
    
    topic_matches = extract_topics_from_full_text(all_content, TOPIC_KEYWORDS)
    full_text_scores = {topic: calculate_full_text_score(matches) for topic, matches in topic_matches.items()}
    
    specific_topic_matches = extract_specific_topics(all_content, SPECIFIC_TOPICS)
    specific_scores = {topic: calculate_specific_score(matches) for topic, matches in specific_topic_matches.items()}
    
    memory_topics = parse_memory_topics(memory_files)
    
    report_lines = []
    report_lines.append("# 📊 Topic Discovery Report")
    report_lines.append("")
    report_lines.append(f"**Review Period:** Last {minutes//60} hours")
    report_lines.append(f"**Sessions Analyzed:** {len(sessions)}")
    report_lines.append(f"**Text Items Processed:** {len(all_content)}")
    report_lines.append(f"**Memory Files:** {len(memory_files)}")
    report_lines.append("")
    
    if full_text_scores:
        report_lines.append("## 🎯 Topics Identified (Full-Text Analysis)")
        report_lines.append("")
        report_lines.append("| # | Topic | Score | Matches |")
        report_lines.append("|---|-------|-------|---------|")
        sorted_topics = sorted(full_text_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (topic, score) in enumerate(sorted_topics, 1):
            match_count = len(topic_matches.get(topic, []))
            stars = "⭐" * score
            report_lines.append(f"| {i} | **{topic}** | {stars} | {match_count} |")
        report_lines.append("")
    
    if specific_scores:
        report_lines.append("## 🎯 Specific Topics (Detailed)")
        report_lines.append("")
        report_lines.append("| # | Topic | Score | Mentions | Article Angles |")
        report_lines.append("|---|-------|-------|----------|----------------|")
        sorted_specific = sorted(specific_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (topic, score) in enumerate(sorted_specific, 1):
            match_count = len(specific_topic_matches.get(topic, []))
            stars = "⭐" * score
            angles = SPECIFIC_TOPICS.get(topic, {}).get('angles', ['General article'])[:2]
            angles_str = '<br>'.join(angles[:2])
            report_lines.append(f"| {i} | **{topic}** | {stars} | {match_count} | {angles_str} |")
        report_lines.append("")
    
    sorted_specific = sorted(specific_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    report_lines.append("## 💡 Writing Recommendations")
    report_lines.append("")
    report_lines.append("Based on the specific topics identified, consider:")
    report_lines.append("")
    for topic, score in sorted_specific:
        if topic in SPECIFIC_TOPICS:
            angles = SPECIFIC_TOPICS[topic].get('angles', [])
            for angle in angles[:2]:
                report_lines.append(f"- **{topic}**: {angle}")
    
    return "\n".join(report_lines)


def main():
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 1440
    print(f"🔍 Discovering topics from last {minutes//60} hours...")
    print()
    report = generate_report(minutes)
    print(report)


if __name__ == "__main__":
    main()
