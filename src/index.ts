import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

/**
 * LogSquash v2.1.0 - Advanced Semantic Compression
 */
class LogCompressor {
  private minLen: number;
  private mode: "lossless" | "semantic";
  private dictionary: Map<string, string> = new Map();
  private reverseDict: Map<string, string> = new Map();
  private counter: number = 0;

  constructor(minLen: number = 10, mode: "lossless" | "semantic" = "semantic") {
    this.minLen = minLen;
    this.mode = mode;
  }

  private getNextKey(): string {
    this.counter++;
    return `#${this.counter}`;
  }

  private normalize(line: string): string {
    if (this.mode === "lossless") return line;
    return line.replace(/\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(,\d+)?Z?/g, "<TS>");
  }

  private getLogLevel(line: string): "ERROR" | "DEBUG" | "INFO" | "OTHER" {
    const upper = line.toUpperCase();
    if (upper.includes("ERROR") || upper.includes("CRITICAL") || upper.includes("FATAL")) return "ERROR";
    if (upper.includes("DEBUG")) return "DEBUG";
    if (upper.includes("INFO")) return "INFO";
    return "OTHER";
  }

  public compress(lines: string[]): { header: string; compressed: string[] } {
    const normalizedLines = lines.map(l => this.normalize(l));
    const lineFrequencies = new Map<string, number>();
    
    // 1. Line Aggregation - Find global duplicates
    for (const line of normalizedLines) {
      lineFrequencies.set(line, (lineFrequencies.get(line) || 0) + 1);
    }

    // Add frequent whole lines to dictionary
    for (const [line, freq] of lineFrequencies.entries()) {
      const level = this.getLogLevel(line);
      const threshold = level === "ERROR" ? 5 : 2; 
      
      const savings = freq * (line.length - 3) - (line.length + 5);
      if (freq >= threshold && savings > 20) {
        if (!this.reverseDict.has(line)) {
          const key = this.getNextKey();
          this.dictionary.set(key, line);
          this.reverseDict.set(line, key);
        }
      }
    }

    // 2. Template Discovery & Phrase matching (N-grams)
    const fragmentCounts = new Map<string, number>();
    for (const line of normalizedLines) {
      if (this.reverseDict.has(line)) continue;

      const rawTokens = line.split(/(\s+|(?=[\[\]\|\{\}\"\',:]+)|(?<=[\[\]\|\{\}\"\',:]+))/).filter(t => t.trim().length > 0);
      for (let len = 2; len <= 5; len++) {
        for (let i = 0; i <= rawTokens.length - len; i++) {
          const phrase = rawTokens.slice(i, i + len).join("");
          if (phrase.trim().length >= this.minLen) {
            fragmentCounts.set(phrase, (fragmentCounts.get(phrase) || 0) + 1);
          }
        }
      }
    }

    // Add frequent phrases to dictionary
    const sortedPhrases = Array.from(fragmentCounts.entries())
      .filter(([phrase, freq]) => {
        const savings = freq * (phrase.length - 3) - (phrase.length + 5);
        return freq >= 2 && savings > 15;
      })
      .sort((a, b) => b[0].length - a[0].length);

    for (const [phrase] of sortedPhrases) {
      if (!this.reverseDict.has(phrase)) {
        const key = this.getNextKey();
        this.dictionary.set(key, phrase);
        this.reverseDict.set(phrase, key);
      }
    }

    // 3. Final Pass - Replace with dictionary keys
    let lastKey = "";
    let repeatCount = 0;
    const finalLines: string[] = [];

    const allPatterns = Array.from(this.reverseDict.keys()).sort((a, b) => b.length - a.length);

    for (const line of normalizedLines) {
      let compressed = line;
      if (this.reverseDict.has(line)) {
        compressed = this.reverseDict.get(line)!;
      } else {
        for (const pattern of allPatterns) {
          if (pattern.length < 15) continue;
          if (compressed.includes(pattern)) {
            const key = this.reverseDict.get(pattern)!;
            compressed = compressed.split(pattern).join(key);
          }
        }
      }

      // Semantic deduplication (Sequential repeats) - Only in semantic mode
      if (this.mode === "semantic" && compressed === lastKey && compressed.startsWith("#")) {
        repeatCount++;
      } else {
        if (repeatCount > 0) {
          finalLines[finalLines.length - 1] += ` (repeated ${repeatCount + 1}x)`;
        }
        finalLines.push(compressed);
        lastKey = compressed;
        repeatCount = 0;
      }
    }
    if (repeatCount > 0) {
      finalLines[finalLines.length - 1] += ` (repeated ${repeatCount + 1}x)`;
    }

    let header = `LOG DICTIONARY (Mode: ${this.mode}):\n`;
    this.dictionary.forEach((val, key) => {
      header += `${key}: ${val}\n`;
    });

    return { header, compressed: finalLines };
  }
}

/**
 * MCP Server Implementation
 */
const server = new Server(
  {
    name: "logsquash",
    version: "2.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const SquashArgumentsSchema = z.object({
  logs: z.string().describe("The log content to squash"),
  mode: z.enum(["lossless", "semantic"]).optional().default("semantic").describe("Compression mode: 'lossless' (preserves time/lines) or 'semantic' (max savings)"),
  minLen: z.number().optional().default(10).describe("Minimum pattern length"),
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "squash_logs",
        description: "Advanced log compression. Choose 'semantic' for max savings or 'lossless' for full precision.",
        inputSchema: {
          type: "object",
          properties: {
            logs: { type: "string" },
            mode: { type: "string", enum: ["lossless", "semantic"], default: "semantic" },
            minLen: { type: "number", default: 10 },
          },
          required: ["logs"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== "squash_logs") {
    throw new Error("Unknown tool");
  }

  const { logs, mode, minLen } = SquashArgumentsSchema.parse(request.params.arguments);
  const lines = logs.split("\n").filter(l => l.trim() !== "");
  
  const compressor = new LogCompressor(minLen, mode as "lossless" | "semantic");
  const { header, compressed } = compressor.compress(lines);

  const result = `${header}\nCOMPRESSED LOGS:\n${compressed.join("\n")}`;

  return {
    content: [
      {
        type: "text",
        text: result,
      },
    ],
  };
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("LogSquash v2.1.0 MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
