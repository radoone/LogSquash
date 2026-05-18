# LogSquash Extension

LogSquash is a token-saving extension for Gemini CLI. It compresses repetitive logs using a dictionary-based approach.

## Skills
- `logsquash`: The primary skill for compressing logs. Activate it using `activate_skill('logsquash')`.

## Tools
- `squash_logs`: Provided by the LogSquash MCP server. Use it to compress log content.

## Workflows
When you encounter large logs in a task:
1.  Check if the `logsquash` skill is active or if the `squash_logs` tool is available.
2.  Compress the logs before processing them to save tokens.
3.  Reference the `LOG DICTIONARY` to maintain accuracy during analysis.
