# LogSquash 🪵🗜️ v2.0

Advanced semantic log compression for Gemini CLI, Codex, and MCP agents. Squashes massive logs into tiny, LLM-readable snippets.

## Why? 🧠

LLM context is expensive and limited. LogSquash identifies patterns and structural redundancy, allowing the model to analyze **10x more history** without losing technical precision.

## New in v2.0 🚀

- **Global Line Aggregation:** Deduplicates identical lines across the entire log stream.
- **Burst Suppression:** Groups consecutive identical logs (e.g., heartbeats) into a single entry: `#1 (repeated 50x)`.
- **Semantic Priority:** Aggressively squashes `DEBUG/INFO` while keeping `ERROR/CRITICAL` more prominent.
- **Template Discovery:** Automatically extracts templates for common log formats.

## Token Efficiency 📈

| Log Type | Compression Ratio | Savings |
|----------|-------------------|---------|
| Repetitive DEBUG/INFO | ~20:1 | **90%** |
| Stack Traces | ~5:1 | **80%** |
| Multi-line JSON | ~4:1 | **75%** |

## How it Works

1. **Aggregation:** Recurring lines are identified and moved to the dictionary.
2. **Template Matching:** Similar lines are parameterized (e.g., `ERROR in #1: #2`).
3. **Sequential deduplication:** Repeats are summarized into a single line with a counter.

## Lossless vs. Lossy ⚖️

LogSquash is designed for **semantic debugging**, not bit-for-bit archiving.

- **Lossless (Preserved):** All log messages, error strings, function names, and **unique trace identifiers** are kept exactly as they appeared. The logical sequence of events is 100% preserved.
- **Lossy (Compressed):** Exact **timestamps** are normalized to `<TS>` to allow pattern matching. Individual timing for each entry in a burst (e.g., `repeated 50x`) is summarized.

**Trade-off:** You lose sub-second timing precision but gain **10x more context** history in your LLM session.

### Example

**Original Logs:**
```text
[2024-05-20 10:00:01] INFO: User login attempt. ID: 123
[2024-05-20 10:00:02] DEBUG: Heartbeat: b'ok'
[2024-05-20 10:00:03] DEBUG: Heartbeat: b'ok'
[2024-05-20 10:00:04] DEBUG: Heartbeat: b'ok'
[2024-05-20 10:00:05] INFO: User login attempt. ID: 123
```

**Squashed Logs (v2.0):**
```text
LOG DICTIONARY:
#1: [<TS>] INFO: User login attempt. ID: 123
#2: [<TS>] DEBUG: Heartbeat: b'ok'

COMPRESSED LOGS:
#1
#2 (repeated 3x)
#1
```

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

## Usage

LogSquash triggers automatically when large logs are detected. You can also manually call it via:

```bash
/squash <log_content>
```

---
*Built for token-conscious engineers.*
