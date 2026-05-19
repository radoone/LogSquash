# LogSquash 🪵🗜️

Token-saving extension for Gemini CLI. Compresses repetitive logs using dictionary-based pattern matching.

## Why?

Logs are repetitive. Repetition wastes tokens. 
LogSquash identifies structural patterns and replaces them with short symbols, allowing the LLM to see **4x more history** in the same context window.

## Token Efficiency 🚀

| Log Type | Raw Size | Squashed | Savings |
|----------|----------|----------|---------|
| Standard Web Logs | 5000 tokens | ~1200 tokens | **~75%** |
| Long Tracebacks | 3000 tokens | ~900 tokens | **~70%** |
| Repetitive JSON | 4000 tokens | ~800 tokens | **~80%** |

## How it Works

1. **Masking:** Replaces volatile data (`<TS>`, `<UUID>`, `<IP>`, `<HEX>`) with semantic placeholders.
2. **Pattern Discovery:** Identifies longest recurring fragments and multi-token phrases.
3. **Dictionary Compression:** Replaces patterns with `#1`, `#2`, etc., and provides a lookup table for the LLM.

### Example

**Original:**
```text
[2026-05-19 10:00:01] ERROR in /usr/src/app/auth.py: Timeout. ID: 550e8400-e29b-41d4-a716-446655440000
[2026-05-19 10:00:05] ERROR in /usr/src/app/auth.py: Timeout. ID: 660f9511-f30c-52e5-b827-557766551111
```

**Squashed:**
```text
LOG DICTIONARY:
#1: /usr/src/app/auth.py
#2: Timeout.

COMPRESSED LOGS:
[<TS>] ERROR in #1: #2 ID: <UUID>
[<TS>] ERROR in #1: #2 ID: <UUID>
```

## Installation

```bash
gemini extension install .
```

## Usage

LogSquash triggers automatically when large logs are detected or when you ask to "analyze logs". You can also manually call it via:

```bash
/squash <log_content>
```

---
*Built for token-conscious engineers.*
