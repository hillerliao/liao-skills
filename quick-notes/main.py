#!/usr/bin/env python3
"""
通用速记技能 - 支持多分类的笔记记录
支持多种日期格式、智能去重、多数据源合并
"""

import os
import sys
import csv
import json
import re
import base64
import ssl
import io
import time
import logging
import hashlib
import shutil
import random
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# Windows 兼容：fcntl 仅在 Unix 系统可用
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# ========== 日志配置 ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== 配置 ==========
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "notes_config.json"
LOCK_FILE = SKILL_DIR / ".lock"

# 默认配置
DEFAULT_CONFIG = {
    "categories": {
        "default": {
            "name": "默认笔记",
            "file": "notes.csv",
            "cloud_path": "/apps/notes/"
        },
        "育儿": {
            "name": "育儿笔记",
            "file": "parenting.csv",
            "cloud_path": "/apps/parenting/"
        },
        "工作": {
            "name": "工作日志",
            "file": "work.csv",
            "cloud_path": "/apps/work/"
        },
        "读书": {
            "name": "读书笔记",
            "file": "books.csv",
            "cloud_path": "/apps/books/"
        }
    },
    "jianguoyun": {
        "host": "dav.jianguoyun.com",
        "base": "/oc-app-data"
    },
    "retry": {
        "max_attempts": 3,
        "backoff_factor": 1
    },
    "backup": {
        "enabled": True,
        "max_count": 5,
        "dir": ".backup"
    }
}

def load_config():
    """加载配置文件"""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, val in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = val
                return config
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
    return DEFAULT_CONFIG

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置失败: {e}")

def get_category_file(category):
    """获取分类对应的文件名"""
    config = load_config()
    cat = config.get("categories", {}).get(category, {})
    if cat:
        return cat.get("file", f"{category}.csv")
    return "notes.csv"

def get_category_cloud_path(category):
    """获取分类对应的云端路径"""
    config = load_config()
    jianguoyun = config.get("jianguoyun", {})
    base = jianguoyun.get("base", "/oc-app-data")
    host = jianguoyun.get("host", "dav.jianguoyun.com")
    
    cat = config.get("categories", {}).get(category, {})
    if cat:
        cloud_sub = cat.get("cloud_path", f"/apps/{category}/")
        return host, f"{base}{cloud_sub}"
    
    return host, f"{base}/apps/"

# ========== ID 生成 ==========
def generate_note_id(date, content):
    """生成笔记 ID：日期 + 内容哈希 + 随机盐（内容短时增加哈希长度）"""
    if not content:
        content = "empty"
    # 内容 < 10 字符时增加哈希长度到 6 位，保证短内容唯一性
    hash_len = 6 if len(content) < 10 else 4
    salt = str(random.randint(100, 999))
    content_hash = hashlib.md5(content.encode()).hexdigest()[:hash_len]
    return f"{date}_{content_hash}{salt}"

# ========== 并发锁 ==========
class FileLock:
    """文件锁实现（支持 Windows 和 Unix）"""
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.fd = None
    
    def __enter__(self):
        self.fd = open(self.lock_file, 'w')
        if HAS_FCNTL:
            fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            if HAS_FCNTL:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()

# ========== 环境与凭证 ==========
def load_env():
    """Load credentials from .env file"""
    env_file = Path.home() / ".openclaw" / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def get_jianguoyun_creds():
    """Get Jianguoyun credentials"""
    email = os.environ.get("JIANGUOYUN_EMAIL", "")
    password = os.environ.get("JIANGUOYUN_PASSWORD", "")
    return email, password

# ========== 日期解析 ==========
def parse_date(date_str):
    """Parse various date formats"""
    today = datetime.now()
    current_year = today.year  # 使用当前年份
    date_str = date_str.strip()
    
    # 2026-03-16
    match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', date_str)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    
    # 3月16日 / 3.16 / 3-16
    match = re.match(r'^(\d{1,2})[月\-\.](\d{1,2})日?$', date_str)
    if match:
        return f"{current_year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
    
    # 今天
    if '今天' in date_str:
        return today.strftime("%Y-%m-%d")
    
    # 昨天
    if '昨天' in date_str:
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")
    
    return None

# ========== 笔记操作 ==========
def get_local_file(category):
    """获取分类对应的本地文件路径"""
    filename = get_category_file(category)
    return SKILL_DIR / filename

def _read_csv_safe(file_path):
    """安全读取 CSV"""
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return list(csv.reader(f))
    except Exception as e:
        logger.error(f"读取CSV失败 {file_path}: {e}")
        return []

def _backup_file(file_path):
    """备份文件到 .backup 目录，保留最近 N 份"""
    if not file_path.exists():
        return
    
    config = load_config()
    backup_config = config.get("backup", DEFAULT_CONFIG["backup"])
    
    if not backup_config.get("enabled", True):
        return
    
    backup_dir = SKILL_DIR / backup_config.get("dir", ".backup")
    backup_dir.mkdir(exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    # 复制文件
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份: {backup_path}")
    except Exception as e:
        logger.warning(f"备份失败: {e}")
        return
    
    # 清理旧备份，保留最近 N 份
    max_count = backup_config.get("max_count", 5)
    pattern = f"{file_path.stem}_*{file_path.suffix}"
    backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    for old_backup in backups[max_count:]:
        try:
            old_backup.unlink()
            logger.info(f"清理旧备份: {old_backup}")
        except Exception as e:
            logger.warning(f"清理备份失败: {e}")

def _write_csv_safe(file_path, rows):
    """安全写入 CSV（原子操作 + 自动备份）"""
    # 先备份原文件
    _backup_file(file_path)
    
    temp_file = file_path.with_suffix('.csv.tmp')
    try:
        with open(temp_file, 'w', encoding='utf-8-sig', newline='') as f:
            csv.writer(f).writerows(rows)
        temp_file.replace(file_path)  # 原子替换
        return True
    except Exception as e:
        logger.error(f"写入CSV失败 {file_path}: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False

def add_note(category, date, content):
    """Add a note to local file"""
    if not content or not content.strip():
        return False
    
    local_file = get_local_file(category)
    
    # Ensure file exists with header
    if not local_file.exists():
        _write_csv_safe(local_file, [['日期', '内容', '分类', 'ID']])
    
    # Generate ID using date + content hash
    note_id = generate_note_id(date, content)
    
    # Read and append
    rows = _read_csv_safe(local_file)
    rows.append([date, content, category, note_id])
    
    return _write_csv_safe(local_file, rows)

def edit_note(category, note_id, new_content):
    """Edit a note by ID"""
    local_file = get_local_file(category)
    if not local_file.exists():
        return False, "文件不存在"
    
    rows = _read_csv_safe(local_file)
    if len(rows) <= 1:
        return False, "无笔记记录"
    
    found = False
    for i, row in enumerate(rows[1:], 1):  # Skip header
        if len(row) >= 4 and row[3].strip() == note_id:
            # Keep original date, update content and regenerate ID
            old_date = row[0].strip()
            new_id = generate_note_id(old_date, new_content)
            rows[i] = [old_date, new_content, category, new_id]
            found = True
            break
    
    if not found:
        return False, f"未找到 ID: {note_id}"
    
    if _write_csv_safe(local_file, rows):
        return True, f"已更新，新 ID: {new_id}"
    return False, "写入失败"

def delete_note(category, note_id):
    """Delete a note by ID"""
    local_file = get_local_file(category)
    if not local_file.exists():
        return False, "文件不存在"
    
    rows = _read_csv_safe(local_file)
    if len(rows) <= 1:
        return False, "无笔记记录"
    
    original_count = len(rows)
    rows = [rows[0]] + [row for row in rows[1:] if not (len(row) >= 4 and row[3].strip() == note_id)]
    
    if len(rows) == original_count:
        return False, f"未找到 ID: {note_id}"
    
    if _write_csv_safe(local_file, rows):
        return True, "已删除"
    return False, "写入失败"

def get_note_by_id(category, note_id):
    """Get a specific note by ID"""
    local_file = get_local_file(category)
    if not local_file.exists():
        return None
    
    for row in _read_csv_safe(local_file)[1:]:
        if len(row) >= 4 and row[3].strip() == note_id:
            return {
                'date': row[0].strip(),
                'content': row[1].strip(),
                'category': row[2].strip(),
                'id': row[3].strip()
            }
    return None

def deduplicate_category(category):
    """Remove duplicate entries for a category"""
    local_file = get_local_file(category)
    rows = _read_csv_safe(local_file)
    
    if len(rows) <= 1:
        return 0
    
    seen = set()
    unique = [rows[0]]  # Keep header
    removed = 0
    
    for row in rows[1:]:  # Skip header
        if len(row) >= 2 and row[0].strip() and row[1].strip():
            # 使用完整内容去重，而不是前50字
            key = (row[0].strip(), row[1].strip())
            if key not in seen:
                seen.add(key)
                unique.append(row)
            else:
                removed += 1
    
    if removed > 0:
        _write_csv_safe(local_file, unique)
    
    return removed

def download_cloud_file(email, password, host, cloud_path, filename):
    """Download a file from Jianguoyun"""
    if not email or not password:
        return None
    
    auth_bytes = base64.b64encode(f"{email}:{password}".encode()).decode()
    url = f"https://{host}{cloud_path}{filename}"
    
    req = urllib.request.Request(
        url,
        method='GET',
        headers={'Authorization': f'Basic {auth_bytes}'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8-sig')
    except Exception as e:
        logger.warning(f"下载失败 {url}: {e}")
        return None

def merge_category(category):
    """Merge cloud sources for a category"""
    email, password = get_jianguoyun_creds()
    if not email or not password:
        return 0, "缺少凭证"
    
    host, cloud_path = get_category_cloud_path(category)
    filename = get_category_file(category)
    local_file = get_local_file(category)
    
    all_notes = {}
    
    # Read local file first
    if local_file.exists():
        for row in _read_csv_safe(local_file)[1:]:  # skip header
            if len(row) >= 2:
                key = (row[0].strip(), row[1].strip())
                all_notes[key] = row
    
    # Try download cloud version
    sources = [filename, f"{filename} - Copy.csv", f"{filename} - Copy (2).csv"]
    for src in sources:
        content = download_cloud_file(email, password, host, cloud_path, src)
        if content:
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                key = (row.get('日期', '').strip(), row.get('内容', '').strip())
                if key not in all_notes:
                    all_notes[key] = row
    
    # Write merged data
    if all_notes:
        rows = [['日期', '内容', '分类', 'ID']]
        for row in all_notes.values():
            rows.append([
                row.get('日期', ''), 
                row.get('内容', ''), 
                row.get('分类', category),
                row.get('ID', '')
            ])
        
        if _write_csv_safe(local_file, rows):
            return len(all_notes), "合并成功"
        return 0, "写入失败"
    return 0, "无数据"

def sync_category_with_retry(category, max_attempts=3):
    """Sync with retry"""
    config = load_config()
    retry_config = config.get("retry", {})
    max_attempts = retry_config.get("max_attempts", max_attempts)
    backoff = retry_config.get("backoff_factor", 1)
    
    email, password = get_jianguoyun_creds()
    if not email or not password:
        return False, "缺少凭证"
    
    local_file = get_local_file(category)
    if not local_file.exists():
        return False, "本地文件不存在"
    
    host, cloud_path = get_category_cloud_path(category)
    filename = get_category_file(category)
    url = f"https://{host}{cloud_path}{filename}"
    
    with open(local_file, 'rb') as f:
        local_data = f.read()
    
    auth_bytes = base64.b64encode(f"{email}:{password}".encode()).decode()
    
    req = urllib.request.Request(
        url,
        data=local_data,
        method='PUT',
        headers={
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    last_error = None
    for attempt in range(max_attempts):
        try:
            with urllib.request.urlopen(req, timeout=10):
                logger.info(f"[{category}] 同步成功")
                return True, "同步成功"
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code}"
            logger.warning(f"[{category}] 同步失败 (尝试 {attempt+1}/{max_attempts}): {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"[{category}] 同步失败 (尝试 {attempt+1}/{max_attempts}): {last_error}")
        
        if attempt < max_attempts - 1:
            time.sleep(backoff * (attempt + 1))  # 指数退避
    
    return False, f"重试{max_attempts}次后失败: {last_error}"

def get_notes_by_date(category, target_date):
    """Get notes for a specific date, returns list of (content, id) tuples"""
    local_file = get_local_file(category)
    if not local_file.exists():
        return []
    
    notes = []
    for row in _read_csv_safe(local_file)[1:]:  # skip header
        if len(row) >= 4 and row[0].strip() == target_date:
            notes.append((row[1].strip(), row[3].strip() if len(row) >= 4 else ""))
    
    return notes

def search_notes(keyword, category=None):
    """Search notes by keyword, optionally filter by category"""
    config = load_config()
    categories = config.get("categories", {})
    
    results = []
    search_cats = [category] if category else list(categories.keys())
    
    for cat in search_cats:
        local_file = get_local_file(cat)
        if not local_file.exists():
            continue
        
        for row in _read_csv_safe(local_file)[1:]:  # skip header
            if len(row) >= 2:
                content = row[1].strip()
                if keyword.lower() in content.lower():
                    note_id = row[3].strip() if len(row) >= 4 else ""
                    date = row[0].strip()
                    results.append((cat, date, content, note_id))
    
    return results

def check_health():
    """Check credentials validity and cloud connectivity"""
    results = []
    
    # 1. 检查环境变量
    email = os.environ.get("JIANGUOYUN_EMAIL", "")
    password = os.environ.get("JIANGUOYUN_PASSWORD", "")
    
    if not email:
        results.append("❌ JIANGUOYUN_EMAIL 未设置")
    else:
        results.append(f"✅ JIANGUOYUN_EMAIL: {email}")
    
    if not password:
        results.append("❌ JIANGUOYUN_PASSWORD 未设置")
    else:
        results.append("✅ JIANGUOYUN_PASSWORD: 已设置")
    
    if not email or not password:
        return "🏥 健康检查结果:\n\n" + "\n".join(results)
    
    # 2. 测试云端连接
    config = load_config()
    jianguoyun = config.get("jianguoyun", {})
    host = jianguoyun.get("host", "dav.jianguoyun.com")
    base = jianguoyun.get("base", "/oc-app-data")
    
    auth_bytes = base64.b64encode(f"{email}:{password}".encode()).decode()
    
    # PROPFIND 请求测试连接
    url = f"https://{host}{base}/"
    body = '<?xml version="1.0" encoding="utf-8"?><propfind xmlns="DAV:"><prop></prop></propfind>'
    
    req = urllib.request.Request(
        url,
        data=body.encode('utf-8'),
        method='PROPFIND',
        headers={
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/xml',
            'Depth': '0'
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in [200, 207]:
                results.append(f"✅ 云端连接正常 ({host})")
            else:
                results.append(f"⚠️ 云端响应异常: HTTP {response.status}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            results.append("❌ 凭证无效：请检查邮箱和应用密码")
        elif e.code == 404:
            results.append(f"⚠️ 云端目录不存在: {base}")
        else:
            results.append(f"❌ 云端连接失败: HTTP {e.code}")
    except Exception as e:
        results.append(f"❌ 云端连接失败: {str(e)}")
    
    # 3. 统计本地数据
    categories = config.get("categories", {})
    total_notes = 0
    for cat in categories.keys():
        local_file = get_local_file(cat)
        if local_file.exists():
            count = len(_read_csv_safe(local_file)) - 1
            if count > 0:
                total_notes += count
    
    results.append(f"📊 本地笔记总数: {total_notes}")
    
    return "🏥 健康检查结果:\n\n" + "\n".join(results)

def add_category(cat_key, cat_name=None):
    """Add a new category"""
    config = load_config()
    categories = config.get("categories", {})
    
    if cat_key in categories:
        return False, f"分类 '{cat_key}' 已存在"
    
    # 创建新分类配置
    categories[cat_key] = {
        "name": cat_name or cat_key,
        "file": f"{cat_key}.csv",
        "cloud_path": f"/apps/{cat_key}/"
    }
    config["categories"] = categories
    save_config(config)
    
    return True, f"已添加分类: {cat_key}"

def delete_category(cat_key):
    """Delete a category (keeps the file)"""
    config = load_config()
    categories = config.get("categories", {})
    
    if cat_key not in categories:
        return False, f"分类 '{cat_key}' 不存在"
    
    if cat_key == "default":
        return False, "不能删除默认分类"
    
    # 获取文件信息
    cat_info = categories[cat_key]
    file_name = cat_info.get("file", f"{cat_key}.csv")
    
    del categories[cat_key]
    config["categories"] = categories
    save_config(config)
    
    # 提示数据文件
    local_file = SKILL_DIR / file_name
    if local_file.exists():
        return True, f"已删除分类: {cat_key}\n⚠️ 数据文件 {file_name} 仍保留，可手动删除"
    return True, f"已删除分类: {cat_key}"

def rename_category(old_key, new_key):
    """Rename a category key"""
    config = load_config()
    categories = config.get("categories", {})
    
    if old_key not in categories:
        return False, f"分类 '{old_key}' 不存在"
    
    if new_key in categories:
        return False, f"分类 '{new_key}' 已存在"
    
    if old_key == "default":
        return False, "不能重命名默认分类"
    
    # 获取旧文件信息
    old_cat = categories[old_key]
    old_file = old_cat.get("file", f"{old_key}.csv")
    new_file = f"{new_key}.csv"
    
    # 重命名配置文件
    categories[new_key] = categories.pop(old_key)
    categories[new_key]["name"] = new_key
    categories[new_key]["file"] = new_file
    categories[new_key]["cloud_path"] = f"/apps/{new_key}/"
    config["categories"] = categories
    save_config(config)
    
    # 重命名本地文件
    old_path = SKILL_DIR / old_file
    new_path = SKILL_DIR / new_file
    if old_path.exists():
        old_path.rename(new_path)
    
    return True, f"已重命名: {old_key} → {new_key}"

def export_notes(fmt="markdown", category=None):
    """Export notes to Markdown, JSON, or HTML format"""
    config = load_config()
    categories = config.get("categories", {})
    
    # 收集所有笔记
    all_notes = []
    export_cats = [category] if category else list(categories.keys())
    
    for cat in export_cats:
        local_file = get_local_file(cat)
        if not local_file.exists():
            continue
        
        for row in _read_csv_safe(local_file)[1:]:
            if len(row) >= 2:
                all_notes.append({
                    'date': row[0].strip(),
                    'content': row[1].strip(),
                    'category': row[2].strip() if len(row) >= 3 else cat,
                    'id': row[3].strip() if len(row) >= 4 else ""
                })
    
    if not all_notes:
        return None, "没有笔记可导出"
    
    # 按日期排序
    all_notes.sort(key=lambda x: x['date'], reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = SKILL_DIR / "exports"
    export_dir.mkdir(exist_ok=True)
    
    if fmt == "markdown" or fmt == "md":
        output_file = export_dir / f"notes_{timestamp}.md"
        content = "# 笔记导出\n\n"
        for note in all_notes:
            content += f"## {note['date']} [{note['category']}]\n\n{note['content']}\n\n---\n\n"
        output_file.write_text(content, encoding='utf-8')
        return output_file, f"已导出 {len(all_notes)} 条笔记"
    
    elif fmt == "json":
        output_file = export_dir / f"notes_{timestamp}.json"
        content = json.dumps(all_notes, ensure_ascii=False, indent=2)
        output_file.write_text(content, encoding='utf-8')
        return output_file, f"已导出 {len(all_notes)} 条笔记"
    
    elif fmt == "html":
        output_file = export_dir / f"notes_{timestamp}.html"
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>笔记导出</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .note { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .date { color: #666; font-size: 14px; }
        .category { background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
        .content { margin-top: 10px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>📝 笔记导出</h1>
"""
        for note in all_notes:
            html += f"""
    <div class="note">
        <div class="date">{note['date']} <span class="category">{note['category']}</span></div>
        <div class="content">{note['content']}</div>
    </div>
"""
        html += "</body></html>"
        output_file.write_text(html, encoding='utf-8')
        return output_file, f"已导出 {len(all_notes)} 条笔记"
    
    return None, f"不支持的格式: {fmt}"

def get_recent_notes(category, days=7):
    """Get notes from recent N days"""
    local_file = get_local_file(category)
    if not local_file.exists():
        return []
    
    notes = []
    today = datetime.now()
    
    for row in _read_csv_safe(local_file)[1:]:  # skip header
        if len(row) >= 2:
            date_str = row[0].strip()
            parsed = parse_date(date_str)
            if parsed:
                try:
                    note_date = datetime.strptime(parsed, "%Y-%m-%d")
                    if 0 <= (today - note_date).days <= days:
                        notes.append((parsed, row[1].strip()))
                except ValueError:
                    pass
    
    return sorted(notes, key=lambda x: x[0], reverse=True)

def list_categories():
    """列出所有可用分类"""
    config = load_config()
    categories = config.get("categories", {})
    
    result = "📂 可用分类:\n\n"
    for key, val in categories.items():
        name = val.get("name", key)
        file = val.get("file", f"{key}.csv")
        local_file = SKILL_DIR / file
        count = 0
        if local_file.exists():
            count = len(_read_csv_safe(local_file)) - 1  # minus header
        result += f"• {key} ({name}) - {count}条\n"
    
    return result

def get_help():
    """获取帮助信息"""
    return """📖 速记技能使用指南

【基础用法】
  #笔记 今天吃了什么      → 记录到默认分类
  育儿 今天吃了什么       → 记录到育儿分类
  2026-03-19,内容        → 指定日期记录

【日期格式】
  2026-03-19,内容        → 完整日期
  3月19日,内容           → 短格式（今年）
  今天                   → 查询今天笔记
  昨天                   → 查询昨天笔记

【命令】
  分类 / list            → 查看所有分类
  搜索 关键词            → 全文搜索
  编辑 ID:xxx 新内容     → 编辑笔记
  删除 ID:xxx           → 删除笔记
  去重 / dedup           → 清理重复
  合并 / merge           → 合并云端数据
  同步 / sync            → 手动同步
  健康检查 / 检查        → 检查云端连接

【分类管理】
  添加分类 名称          → 新增分类
  删除分类 名称          → 删除分类
  重命名 旧名 新名       → 重命名分类

【导出】
  导出 markdown         → 导出为 Markdown
  导出 json              → 导出为 JSON
  导出 html              → 导出为 HTML
"""

# ========== 主处理函数 ==========
def handle_input(user_input):
    """Main handler for user input"""
    logger.info(f"收到请求: {user_input[:50]}...")
    
    load_env()
    
    # 移除触发词
    user_input = re.sub(r'^#笔记\s*', '', user_input)
    user_input = re.sub(r'^#育儿笔记\s*', '', user_input)
    user_input = re.sub(r'^速记\s*', '', user_input)
    user_input = user_input.strip()
    
    if not user_input:
        return list_categories()
    
    # 解析分类 - 使用更精确的匹配
    category = "default"
    config = load_config()
    categories = config.get("categories", {})
    
    # 按长度降序排列，优先匹配更长的分类名
    sorted_cats = sorted(categories.keys(), key=len, reverse=True)
    for cat in sorted_cats:
        if user_input.startswith(f"{cat} "):
            category = cat
            user_input = user_input[len(cat):].strip()
            break
    
    # 特殊命令
    if user_input in ['去重', 'dedup']:
        with FileLock(LOCK_FILE):
            removed = deduplicate_category(category)
        return f"✅ [{category}] 已清理重复记录 {removed} 条"
    
    if user_input in ['合并', 'merge']:
        with FileLock(LOCK_FILE):
            count, msg = merge_category(category)
        return f"✅ [{category}] {msg}，共 {count} 条"
    
    if user_input in ['同步', 'sync']:
        success, msg = sync_category_with_retry(category)
        if success:
            return f"☁️ [{category}] {msg}"
        return f"❌ [{category}] {msg}"
    
    if user_input in ['分类', 'categories', 'list']:
        return list_categories()
    
    if user_input in ['help', '帮助', '?']:
        return get_help()
    
    # 编辑命令: [分类] 编辑 ID:xxx 新内容
    match = re.search(r'编辑\s+ID[:：]?\s*(\S+)\s+(.+)$', user_input)
    if match:
        note_id = match.group(1)
        new_content = match.group(2).strip()
        edit_cat = category  # 使用已解析的分类
        with FileLock(LOCK_FILE):
            success, msg = edit_note(edit_cat, note_id, new_content)
        if success:
            sync_category_with_retry(edit_cat)
            return f"✅ [{edit_cat}] {msg}"
        return f"❌ [{edit_cat}] {msg}"
    
    # 删除命令: [分类] 删除 ID:xxx
    match = re.search(r'删除\s+ID[:：]?\s*(\S+)$', user_input)
    if match:
        note_id = match.group(1)
        delete_cat = category  # 使用已解析的分类
        with FileLock(LOCK_FILE):
            success, msg = delete_note(delete_cat, note_id)
        if success:
            sync_category_with_retry(delete_cat)
            return f"✅ [{delete_cat}] {msg}"
        return f"❌ [{delete_cat}] {msg}"
    
    # 搜索命令: 搜索 关键词
    match = re.search(r'搜索\s+(.+)$', user_input)
    if match:
        keyword = match.group(1).strip()
        # 判断是否在分类后搜索（格式：分类 搜索 关键词）
        search_cat = category if category != "default" else None
        results = search_notes(keyword, search_cat)
        if results:
            result = f"🔍 搜索 \"{keyword}\" 找到 {len(results)} 条:\n\n"
            for cat, date, content, note_id in results[:20]:  # 限制显示前20条
                result += f"📅 {date} [{cat}]\n📝 {content[:50]}{'...' if len(content) > 50 else ''}\n🆔 {note_id}\n\n"
            if len(results) > 20:
                result += f"... 还有 {len(results) - 20} 条结果"
            return result
        return f"🔍 未找到包含 \"{keyword}\" 的笔记"
    
    # 健康检查命令
    if user_input in ['健康检查', '检查', 'health']:
        load_env()  # 确保加载环境变量
        return check_health()
    
    # 添加分类: 添加分类 名称
    match = re.match(r'^添加分类\s+(\S+)(?:\s+(.+))?$', user_input)
    if match:
        cat_key = match.group(1)
        cat_name = match.group(2)
        success, msg = add_category(cat_key, cat_name)
        return f"✅ {msg}" if success else f"❌ {msg}"
    
    # 删除分类: 删除分类 名称
    match = re.match(r'^删除分类\s+(\S+)$', user_input)
    if match:
        cat_key = match.group(1)
        success, msg = delete_category(cat_key)
        return f"✅ {msg}" if success else f"❌ {msg}"
    
    # 重命名分类: 重命名 分类 新名称
    match = re.match(r'^重命名\s+(\S+)\s+(\S+)$', user_input)
    if match:
        old_key = match.group(1)
        new_key = match.group(2)
        success, msg = rename_category(old_key, new_key)
        return f"✅ {msg}" if success else f"❌ {msg}"
    
    # 导出命令: 导出 markdown/json/html
    match = re.search(r'导出\s+(markdown|md|json|html)$', user_input.lower())
    if match:
        fmt = match.group(1)
        if fmt == "md":
            fmt = "markdown"
        export_cat = category if category != "default" else None
        output_file, msg = export_notes(fmt, export_cat)
        if output_file:
            return f"✅ {msg}\n📁 {output_file}"
        return f"❌ {msg}"
    
    # 解析日期和内容
    # 格式1: 2026-03-16,内容
    match = re.match(r'^(\d{4}-\d{2}-\d{2})[,，、\s]+(.+)', user_input)
    if match:
        date = match.group(1)
        content = match.group(2).strip()
        
        with FileLock(LOCK_FILE):
            add_note(category, date, content)
            deduplicate_category(category)
        
        success, msg = sync_category_with_retry(category)
        
        result = f"✅ 已添加到 [{category}]！\n📅 {date}\n📝 {content}"
        if success:
            result += "\n☁️ 已同步"
        return result
    
    # 格式2: 3月16日,内容
    match = re.match(r'^(\d{1,2})月(\d{1,2})日[,，、\s]+(.+)', user_input)
    if match:
        date = f"{datetime.now().year}-{int(match.group(1)):02d}-{int(match.group(2)):02d}"
        content = match.group(3).strip()
        
        with FileLock(LOCK_FILE):
            add_note(category, date, content)
            deduplicate_category(category)
        
        success, msg = sync_category_with_retry(category)
        
        result = f"✅ 已添加到 [{category}]！\n📅 {date}\n📝 {content}"
        if success:
            result += "\n☁️ 已同步"
        return result
    
    # 格式3: 只有日期（查询）
    parsed_date = parse_date(user_input)
    if parsed_date and len(user_input) < 20:
        notes = get_notes_by_date(category, parsed_date)
        if notes:
            result = f"📅 [{category}] {parsed_date} ({len(notes)}条):\n\n"
            for i, (content, note_id) in enumerate(notes, 1):
                result += f"{i}. {content}\n   🆔 {note_id}\n"
            return result
        else:
            return f"📅 [{category}] {parsed_date} 无记录"
    
    # 默认: 今天日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    with FileLock(LOCK_FILE):
        add_note(category, today, user_input)
        deduplicate_category(category)
    
    success, msg = sync_category_with_retry(category)
    
    result = f"✅ 已添加到 [{category}]！\n📅 {today}\n📝 {user_input}"
    if success:
        result += "\n☁️ 已同步"
    return result

# ========== 入口 ==========
if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = sys.stdin.read().strip()
    
    if user_input:
        print(handle_input(user_input))
