# file-organizer-ai-mcp

MCP server for file organization tools.

## Tools

- **categorize_by_extension** — Categorize files by type (images, code, docs, etc.)
- **find_duplicates_by_hash** — Find duplicate files via MD5 hash
- **calculate_directory_size** — Directory size breakdown by subdirectory
- **generate_tree** — Generate directory tree view

## Usage

```bash
pip install mcp
python server.py
```

## Rate Limits

50 calls/day per tool (free tier).
