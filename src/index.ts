import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

/**
 * LogSquash Compression Logic
 */
class LogCompressor {
  private minLen: number;
  private minFreq: number;
  private dictionary: Map<string, string> = new Map();
  private reverseDict: Map<string, string> = new Map();
  private counter: number = 0;

  constructor(minLen: number = 10, minFreq: number = 2) {
    this.minLen = minLen;
    this.minFreq = minFreq;
  }

  private getNextKey(): string {
    this.counter++;
    return `#${this.counter}`;
  }

  private findPatterns(lines: string[]): string[] {
    const fragmentCounts = new Map<string, number>();

    for (const line of lines) {
      // Remove timestamps to find structural repetitions
      const cleanLine = line.replace(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(,\d+)?/g, "<TS>");
      
      // Split by common separators to find repeating fragments
      const parts = line.split(/[\[\]\|]/);
      for (let part of parts) {
        part = part.trim();
        if (part.length >= this.minLen) {
          fragmentCounts.set(part, (fragmentCounts.get(part) || 0) + 1);
        }
      }

      // Also try the message body
      const msgPart = line.replace(/^.*?\] /, "");
      if (msgPart.length >= this.minLen) {
        fragmentCounts.set(msgPart, (fragmentCounts.get(msgPart) || 0) + 1);
      }
    }

    // Filter and sort by length descending
    return Array.from(fragmentCounts.entries())
      .filter(([_, freq]) => freq >= this.minFreq)
      .map(([text]) => text)
      .sort((a, b) => b.length - a.length);
  }

  public compress(lines: string[]): { header: string; compressed: string[] } {
    const patterns = this.findPatterns(lines);
    
    for (const pattern of patterns) {
      if (!this.reverseDict.has(pattern)) {
        const key = this.getNextKey();
        this.dictionary.set(key, pattern);
        this.reverseDict.set(pattern, key);
      }
    }

    const compressedLines = lines.map(line => {
      let compressed = line;
      for (const pattern of patterns) {
        const key = this.reverseDict.get(pattern)!;
        // Use global regex for all occurrences
        compressed = compressed.split(pattern).join(key);
      }
      return compressed;
    });

    let header = "LOG DICTIONARY:\n";
    this.dictionary.forEach((val, key) => {
      header += `${key}: ${val}\n`;
    });

    return { header, compressed: compressedLines };
  }
}

/**
 * MCP Server Implementation
 */
const server = new Server(
  {
    name: "logsquash",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const SquashArgumentsSchema = z.object({
  logs: z.string().describe("The log content to squash"),
  minLen: z.number().optional().default(10).describe("Minimum pattern length to compress"),
  minFreq: z.number().optional().default(2).describe("Minimum frequency of pattern to compress"),
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "squash_logs",
        description: "Squash repetitive logs into a dictionary-based compressed format to save tokens.",
        inputSchema: {
          type: "object",
          properties: {
            logs: { type: "string" },
            minLen: { type: "number" },
            minFreq: { type: "number" },
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

  const { logs, minLen, minFreq } = SquashArgumentsSchema.parse(request.params.arguments);
  const lines = logs.split("\n").filter(l => l.trim() !== "");
  
  const compressor = new LogCompressor(minLen, minFreq);
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
  console.error("LogSquash MCP server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
