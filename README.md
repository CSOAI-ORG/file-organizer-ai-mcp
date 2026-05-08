<div align="center">

# File Organizer Ai MCP

**File Organizer AI MCP Server — File organization tools.**

[![PyPI](https://img.shields.io/pypi/v/meok-file-organizer-ai-mcp)](https://pypi.org/project/meok-file-organizer-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

File Organizer AI MCP Server — File organization tools.

## Tools

| Tool | Description |
|------|-------------|
| `categorize_by_extension` | Categorize files in a directory by their extensions. |
| `find_duplicates_by_hash` | Find duplicate files by comparing MD5 hashes. |
| `calculate_directory_size` | Calculate directory size with breakdown by subdirectory. |
| `generate_tree` | Generate a tree view of a directory structure. |

## Installation

```bash
pip install meok-file-organizer-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "file-organizer-ai": {
      "command": "python",
      "args": ["-m", "meok_file_organizer_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
