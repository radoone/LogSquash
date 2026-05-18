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
The easiest way to install LogSquash is using our one-liner install script:
```bash
curl -sSL https://raw.githubusercontent.com/radoone/LogSquash/main/install.sh | bash
```

Or manually:
1. Clone this repository into your Gemini extensions folder:
   ```bash
   git clone https://github.com/radoone/LogSquash.git ~/.gemini/extensions/logsquash
   ```
2. Navigate to the folder and build:
   ```bash
   cd ~/.gemini/extensions/logsquash
   npm install && npm run build
   ```
3. Restart Gemini CLI. The `logsquash` skill and `squash_logs` tool will now be available.

### Claude Desktop / Cursor / Other Agents
Configure the agent to use the MCP server by pointing it to the built `dist/index.js` file.

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