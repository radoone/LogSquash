# LogSquash 🪵🗜️

**Put your logs on a token diet before feeding them to AI.**

LogSquash is a lightweight **Model Context Protocol (MCP)** server that squashes repetitive noise in your logs into tiny reference keys. It saves massive amounts of context window space (**30-70% token savings**) without losing critical diagnostic information.

Perfect for **Gemini CLI, Claude Code, Cursor, Windsurf**, and any other agent supporting the MCP protocol.

## Why LogSquash?

*   💸 **Slash AI API Costs**: Logs are notoriously repetitive. Replace 50-character recurring strings with 2-character keys (`#1`).
*   🧠 **Maximize Context Windows**: Fit 3x more log history into a single prompt.
*   🎯 **Enhance AI Focus**: Removing visual noise and boilerplate helps LLMs focus on specific errors and anomalies.
*   ⚡ **Zero Model Overhead**: Pure, fast text-processing heuristic. No extra API calls needed for compression.

## Install

LogSquash works natively with all modern AI coding assistants. 

### Per-Agent Install Commands

| Agent | Install command | Note |
|---|---|---|
| **Gemini CLI** | `gemini extensions install https://github.com/radoone/LogSquash --auto-update` | Native extension. Auto-activates MCP server and skill. |
| **Codex CLI** | `codex extensions install https://github.com/radoone/LogSquash --auto-update` | Native extension. Auto-activates MCP server and skill. |
| **Cursor** | `npx skills add radoone/LogSquash -a cursor` | Requires manual MCP setup (see below). |
| **Windsurf** | `npx skills add radoone/LogSquash -a windsurf` | Requires manual MCP setup (see below). |
| **GitHub Copilot** | `npx skills add radoone/LogSquash -a copilot` | Requires manual MCP setup (see below). |
| **Cline** | `npx skills add radoone/LogSquash -a cline` | Requires manual MCP setup (see below). |

*If your agent isn't listed above but supports Vercel's `npx skills`, you can try `npx skills add radoone/LogSquash -a <agent-name>`.*

### Manual MCP Setup

For agents that don't auto-configure MCP servers via extensions (like Cursor, Copilot, Windsurf, or Claude Desktop), you need to tell them how to run the LogSquash server.

Since LogSquash is published to GitHub and executable via `npx`, you don't even need to clone the repository. Just add this to your agent's MCP configuration file (e.g., `.vscode/mcp.json` for Copilot, or `claude_desktop_config.json`):

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

For **Cursor** and **Windsurf** settings UI:
- **Type**: `stdio`
- **Name**: `logsquash`
- **Command**: `npx -y github:radoone/LogSquash`

## License
MIT