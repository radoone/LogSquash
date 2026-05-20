# LogSquash 🪵🗜️ v2.1.0

Advanced semantic log compression for Gemini CLI, Codex, and MCP agents. Squashes massive logs into tiny, LLM-readable snippets.

## Why? 🧠

LLM context is expensive and limited. LogSquash identifies patterns and structural redundancy, allowing the model to analyze **10x more history** without losing technical precision.

## New in v2.1.0 🚀

- **Multi-Mode Compression:** Toggle between `semantic` (max savings) and `lossless` (full precision).
- **Global Line Aggregation:** Deduplicates identical lines across the entire log stream.
- **Burst Suppression:** Groups consecutive identical logs (e.g., heartbeats) into a single entry: `#1 (repeated 50x)`.
- **Semantic Priority:** Aggressively squashes `DEBUG/INFO` while keeping `ERROR/CRITICAL` more prominent.

## Compression Modes ⚖️

| Mode | Savings | Preserves Timestamps | Summarizes Repeats | Best For |
|------|---------|----------------------|--------------------|----------|
| `semantic` (default) | **~90%** | No (`<TS>`) | Yes | General debugging, large history |
| `lossless` | **~40%** | Yes | No | Detailed timing analysis, audit logs |

## How it Works

1. **Aggregation:** Recurring lines are identified and moved to the dictionary.
2. **Template Matching:** Similar lines are parameterized (e.g., `ERROR in #1: #2`).
3. **Burst Suppression:** Sequential repeats are summarized (Semantic mode only).

## Installation

### ♊ Gemini CLI
```bash
gemini extension install https://github.com/radoone/LogSquash
```

### 💻 Codex (VS Code)
1. Open Codex Extension settings.
2. Add a new MCP Server:
   - **Name:** `logsquash`
   - **Command:** `node`
   - **Arguments:** `["/path/to/LogSquash/dist/index.js"]`

### 🤖 Custom MCP Config
```json
{
  "mcpServers": {
    "logsquash": {
      "command": "node",
      "args": ["/path/to/LogSquash/dist/index.js"]
    }
  }
}
```

## Usage

LogSquash triggers automatically when large logs are detected. You can also manually toggle modes:

```bash
/squash <log_content> mode=lossless
```

---
*Built for token-conscious engineers.*
