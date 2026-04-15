"""File Organizer AI MCP Server — File organization tools."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import hashlib
import os
import time
from typing import Any
from mcp.server.fastmcp import FastMCP

import json
from datetime import datetime, timezone
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None


mcp = FastMCP("file-organizer-ai", instructions="MEOK AI Labs MCP Server")
_calls: dict[str, list[float]] = {}
DAILY_LIMIT = 50

def _rate_check(tool: str) -> bool:
    now = time.time()
    _calls.setdefault(tool, [])
    _calls[tool] = [t for t in _calls[tool] if t > now - 86400]
    if len(_calls[tool]) >= DAILY_LIMIT:
        return False
    _calls[tool].append(now)
    return True

CATEGORIES = {
    "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".csv", ".pptx"],
    "code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".rs", ".go", ".rb", ".php", ".swift", ".kt"],
    "web": [".html", ".css", ".scss", ".less", ".json", ".xml", ".yaml", ".yml", ".toml"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "archives": [".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz"],
    "data": [".db", ".sqlite", ".sql", ".parquet", ".feather", ".hdf5"],
    "config": [".env", ".ini", ".cfg", ".conf", ".properties"],
    "fonts": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
}

def _categorize(ext: str) -> str:
    ext = ext.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "other"

@mcp.tool()
def categorize_by_extension(directory: str, api_key: str = "") -> dict[str, Any]:
    """Categorize files in a directory by their extensions."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not _rate_check("categorize_by_extension"):
        return {"error": "Rate limit exceeded (50/day)"}
    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}"}
    result: dict[str, list[str]] = {}
    ext_counts: dict[str, int] = {}
    total_size = 0
    file_count = 0
    for entry in os.scandir(directory):
        if entry.is_file():
            file_count += 1
            ext = os.path.splitext(entry.name)[1]
            cat = _categorize(ext)
            result.setdefault(cat, []).append(entry.name)
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            try:
                total_size += entry.stat().st_size
            except OSError:
                pass
    # Sort categories by file count
    sorted_cats = {k: v for k, v in sorted(result.items(), key=lambda x: -len(x[1]))}
    top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "categories": {k: {"files": v[:20], "count": len(v)} for k, v in sorted_cats.items()},
        "total_files": file_count, "total_size_bytes": total_size,
        "total_size_human": _human_size(total_size),
        "top_extensions": dict(top_exts)
    }

def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024  # type: ignore
    return f"{size:.1f} PB"

@mcp.tool()
def find_duplicates_by_hash(directory: str, recursive: bool = False, api_key: str = "") -> dict[str, Any]:
    """Find duplicate files by comparing MD5 hashes."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not _rate_check("find_duplicates_by_hash"):
        return {"error": "Rate limit exceeded (50/day)"}
    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}"}
    hashes: dict[str, list[str]] = {}
    errors = []
    scanned = 0
    if recursive:
        for root, dirs, files in os.walk(directory):
            for f in files:
                path = os.path.join(root, f)
                scanned += 1
                if scanned > 10000:
                    break
                try:
                    h = hashlib.md5(open(path, "rb").read(8192)).hexdigest()
                    hashes.setdefault(h, []).append(path)
                except (OSError, PermissionError):
                    errors.append(path)
    else:
        for entry in os.scandir(directory):
            if entry.is_file():
                scanned += 1
                try:
                    h = hashlib.md5(open(entry.path, "rb").read(8192)).hexdigest()
                    hashes.setdefault(h, []).append(entry.path)
                except (OSError, PermissionError):
                    errors.append(entry.path)
    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    wasted = 0
    for paths in duplicates.values():
        try:
            size = os.path.getsize(paths[0])
            wasted += size * (len(paths) - 1)
        except OSError:
            pass
    return {
        "duplicates": [{"hash": h, "files": p, "count": len(p)} for h, p in list(duplicates.items())[:50]],
        "duplicate_groups": len(duplicates),
        "total_duplicate_files": sum(len(p) for p in duplicates.values()),
        "wasted_space": _human_size(wasted),
        "files_scanned": scanned, "errors": len(errors)
    }

@mcp.tool()
def calculate_directory_size(directory: str, top_n: int = 10, api_key: str = "") -> dict[str, Any]:
    """Calculate directory size with breakdown by subdirectory."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not _rate_check("calculate_directory_size"):
        return {"error": "Rate limit exceeded (50/day)"}
    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}"}
    total = 0
    file_count = 0
    dir_count = 0
    subdir_sizes: dict[str, int] = {}
    ext_sizes: dict[str, int] = {}
    for root, dirs, files in os.walk(directory):
        dir_count += len(dirs)
        for f in files:
            file_count += 1
            path = os.path.join(root, f)
            try:
                size = os.path.getsize(path)
                total += size
                rel = os.path.relpath(root, directory)
                top_dir = rel.split(os.sep)[0] if rel != "." else "."
                subdir_sizes[top_dir] = subdir_sizes.get(top_dir, 0) + size
                ext = os.path.splitext(f)[1].lower()
                ext_sizes[ext] = ext_sizes.get(ext, 0) + size
            except OSError:
                pass
    top_dirs = sorted(subdir_sizes.items(), key=lambda x: -x[1])[:top_n]
    top_exts = sorted(ext_sizes.items(), key=lambda x: -x[1])[:top_n]
    return {
        "directory": directory, "total_size": total, "total_size_human": _human_size(total),
        "file_count": file_count, "dir_count": dir_count,
        "top_directories": [{"name": n, "size": s, "human": _human_size(s), "pct": round(s/max(total,1)*100, 1)} for n, s in top_dirs],
        "top_extensions": [{"ext": e, "size": s, "human": _human_size(s)} for e, s in top_exts]
    }

@mcp.tool()
def generate_tree(directory: str, max_depth: int = 3, show_size: bool = False, api_key: str = "") -> dict[str, Any]:
    """Generate a tree view of a directory structure."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(): return err

    if not _rate_check("generate_tree"):
        return {"error": "Rate limit exceeded (50/day)"}
    if not os.path.isdir(directory):
        return {"error": f"Not a directory: {directory}"}
    lines = [os.path.basename(directory) + "/"]
    file_count = 0
    dir_count = 0
    def _tree(path: str, prefix: str, depth: int):
        nonlocal file_count, dir_count
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        visible = [e for e in entries if not e.name.startswith(".")]
        for i, entry in enumerate(visible):
            is_last = i == len(visible) - 1
            connector = "`-- " if is_last else "|-- "
            size_str = ""
            if show_size and entry.is_file():
                try:
                    size_str = f" ({_human_size(entry.stat().st_size)})"
                except OSError:
                    pass
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}{size_str}")
            if entry.is_dir():
                dir_count += 1
                ext = "    " if is_last else "|   "
                _tree(entry.path, prefix + ext, depth + 1)
            else:
                file_count += 1
    _tree(directory, "", 1)
    tree_str = "\n".join(lines[:500])  # Cap output
    return {"tree": tree_str, "file_count": file_count, "dir_count": dir_count, "max_depth": max_depth, "truncated": len(lines) > 500}

if __name__ == "__main__":
    mcp.run()
