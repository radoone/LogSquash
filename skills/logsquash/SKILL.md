---
name: logsquash
description: Squash repetitive logs into a dictionary-based compressed format to save tokens. Use when the user provides large logs or when context limits are being reached.
---

# LogSquash 🪵🗜️

This skill allows the agent to compress large, repetitive log files using the LogSquash MCP server. This saves tokens and expands the effective context window.

## Instructions
1.  **Identify Logs**: Locate the log file or text that needs analysis.
2.  **Squash**: Call the `squash_logs` tool via the LogSquash MCP server.
3.  **Analyze**: Use the compressed output (and the provided LOG DICTIONARY) to perform your debugging or analysis task.

## Example
"I've squashed the logs to save tokens. Based on the dictionary (#1 = Connection Timeout), I can see that the service failed 50 times in the last hour..."
