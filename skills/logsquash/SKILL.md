# Skill: LogSquash 🪵🗜️

This skill allows the agent to compress large, repetitive log files using the LogSquash MCP server. This saves tokens and expands the effective context window.

## When to use
- When the user provides a large log file for analysis.
- When log-heavy terminal output is being processed.
- When you are hitting context window limits due to verbose diagnostics.

## Instructions
1.  **Identify Logs**: Locate the log file or text that needs analysis.
2.  **Squash**: Call the `squash_logs` tool via the LogSquash MCP server.
3.  **Analyze**: Use the compressed output (and the provided LOG DICTIONARY) to perform your debugging or analysis task.

## Example
"I've squashed the logs to save tokens. Based on the dictionary (#1 = Connection Timeout), I can see that the service failed 50 times in the last hour..."
