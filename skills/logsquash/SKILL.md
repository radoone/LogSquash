---
name: logsquash
description: Squash repetitive logs into a dictionary-based compressed format to save tokens. Use /squash or /logsquash to manually trigger.
---

# LogSquash 🪵🗜️

This skill allows the agent to compress large, repetitive log files using the LogSquash MCP server. This saves tokens and expands the effective context window.

## Commands
Recognize and handle the following slash commands:
- `/squash <logs> [mode=semantic|lossless]`
- `/logsquash <logs> [mode=semantic|lossless]`

## Instructions
1.  **Trigger**: If the user uses a slash command or asks to "squash" or "analyze logs", call the `squash_logs` tool.
2.  **Parameter Parsing**:
    - Extract the log content from the message.
    - If `mode=lossless` is present, pass `mode: "lossless"` to the tool.
    - Otherwise, default to `mode: "semantic"`.
3.  **Analyze**: Use the compressed output (and the provided LOG DICTIONARY) to perform your debugging or analysis task.

## Example
User: `/squash [2026-05-19 INFO] ... mode=lossless`
Agent: *Calls `squash_logs(logs: "...", mode: "lossless")`*
"I've squashed the logs in lossless mode..."
