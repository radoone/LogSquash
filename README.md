# LogSquash 🪵🗜️

**Put your logs on a token diet before feeding them to AI.**

LogSquash is a lightweight **Model Context Protocol (MCP)** server that squashes repetitive noise in your logs into tiny reference keys. It saves massive amounts of context window space (**30-70% token savings**) without losing critical diagnostic information.

Perfect for **Gemini CLI, Claude Code, Cursor, Windsurf**, and any other agent supporting the MCP protocol.

## Why LogSquash?

*   💸 **Slash AI API Costs**: Logs are notoriously repetitive. Replace 50-character recurring strings with 2-character keys (`#1`).
*   🧠 **Maximize Context Windows**: Fit 3x more log history into a single prompt.
*   🎯 **Enhance AI Focus**: Removing visual noise and boilerplate helps LLMs focus on specific errors and anomalies.
*   ⚡ **Zero Model Overhead**: Pure, fast text-processing heuristic. No extra API calls needed for compression.

## Integration

Because LogSquash is built on the **Model Context Protocol (MCP)**, it works natively with all modern AI coding assistants.

### GitHub Copilot (VS Code / Visual Studio)
Copilot supports MCP natively in "Agent Mode".
1. In VS Code, create a file at `.vscode/mcp.json` (or use the global MCP config).
2. Add the LogSquash server configuration:
```json
{
  "mcpServers": {
    "logsquash": {
      "command": "node",
      "args": ["/absolute/path/to/LogSquash/dist/index.js"]
    }
  }
}
```

### Cursor & Windsurf
Cursor and Windsurf support MCP servers directly through their settings UI.
1. Open Settings -> Features -> MCP (or Context).
2. Add a new MCP server:
   - **Type**: `stdio`
   - **Name**: `logsquash`
   - **Command**: `node /absolute/path/to/LogSquash/dist/index.js`

### Claude Desktop
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "logsquash": {
      "command": "node",
      "args": ["/absolute/path/to/LogSquash/dist/index.js"]
    }
  }
}
```

### Gemini CLI (Native Extension)
LogSquash is natively supported by Gemini CLI. Install it directly using:
```bash
gemini extensions install https://github.com/radoone/LogSquash --auto-update
```
The `--auto-update` flag ensures Gemini CLI will automatically fetch new versions when they are released. Restart Gemini CLI to activate the `logsquash` skill and `squash_logs` tool.

### Codex CLI (Native Extension)
LogSquash is natively supported by Codex CLI. Install it directly using:
```bash
codex extensions install https://github.com/radoone/LogSquash --auto-update
```
Restart Codex CLI to activate the `logsquash` skill and `squash_logs` tool.

### GitHub Copilot (VS Code)
1. Add the MCP server to your `.vscode/mcp.json` or global VS Code MCP configuration:
```json
{
  "mcpServers": {
    "logsquash": {
      "command": "npx",
      "args": ["-y", "github:radoone/LogSquash"]
    }
  }
}
```
2. *(Optional)* Add the skill instructions so Copilot knows *when* to use it:
```bash
npx skills add radoone/LogSquash -a copilot
```

## Features
- **`squash_logs` tool**: Automatically identifies repeating patterns and replaces them with short dictionary keys.
- **LLM-Ready Output**: Prepends a `LOG DICTIONARY` to the squashed logs, which LLMs natively understand.

## Installation & Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Build the project:
   ```bash
   npm run build
   ```
4. Run locally (optional):
   ```bash
   node dist/index.js
   ```

## License
MIT