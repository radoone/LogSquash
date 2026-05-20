
class LogCompressor {
  constructor(minLen = 10) {
    this.minLen = minLen;
    this.dictionary = new Map();
    this.reverseDict = new Map();
    this.counter = 0;
  }

  getNextKey() {
    this.counter++;
    return `#${this.counter}`;
  }

  normalize(line) {
    return line.replace(/\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(,\d+)?Z?/g, "<TS>");
  }

  getLogLevel(line) {
    const upper = line.toUpperCase();
    if (upper.includes("ERROR") || upper.includes("CRITICAL") || upper.includes("FATAL")) return "ERROR";
    if (upper.includes("DEBUG")) return "DEBUG";
    if (upper.includes("INFO")) return "INFO";
    return "OTHER";
  }

  compress(lines) {
    const normalizedLines = lines.map(l => this.normalize(l));
    const lineFrequencies = new Map();
    
    // 1. Line Aggregation - Find global duplicates
    for (const line of normalizedLines) {
      lineFrequencies.set(line, (lineFrequencies.get(line) || 0) + 1);
    }

    // Add frequent whole lines to dictionary
    for (const [line, freq] of lineFrequencies.entries()) {
      const level = this.getLogLevel(line);
      const threshold = level === "ERROR" ? 5 : 2; // Be less aggressive with errors
      
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
    const fragmentCounts = new Map();
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
    const finalLines = [];

    const allPatterns = Array.from(this.reverseDict.keys()).sort((a, b) => b.length - a.length);

    for (const line of normalizedLines) {
      let compressed = line;
      if (this.reverseDict.has(line)) {
        compressed = this.reverseDict.get(line);
      } else {
        for (const pattern of allPatterns) {
          if (pattern.length < 15) continue;
          if (compressed.includes(pattern)) {
            const key = this.reverseDict.get(pattern);
            compressed = compressed.split(pattern).join(key);
          }
        }
      }

      if (compressed === lastKey && compressed.startsWith("#")) {
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

    let header = "LOG DICTIONARY:\n";
    this.dictionary.forEach((val, key) => {
      header += `${key}: ${val}\n`;
    });

    return { header, compressed: finalLines };
  }
}

// SIMULATE MASSIVE LOG
const baseLines = [
  "[2026-05-19 14:00:01 - system - INFO] System boot sequence started.",
  "[2026-05-19 14:00:02 - worker - DEBUG] Processing task-12345",
  "[2026-05-19 14:00:03 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:04 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:05 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:06 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:07 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:08 - worker - DEBUG] Processing task-12345",
  "[2026-05-19 14:00:09 - system - INFO] System boot sequence started.",
  "[2026-05-19 14:00:10 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:11 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:12 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:13 - api - ERROR] Connection refused to database at 10.0.0.50:5432",
  "[2026-05-19 14:00:14 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:15 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:16 - worker - DEBUG] Processing task-12345",
  "[2026-05-19 14:00:17 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:18 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:19 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:20 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:21 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:22 - api - ERROR] Connection refused to database at 10.0.0.50:5432",
  "[2026-05-19 14:00:23 - system - INFO] System boot sequence started.",
  "[2026-05-19 14:00:24 - monitor - DEBUG] ping: heartbeat ok",
  "[2026-05-19 14:00:25 - monitor - DEBUG] ping: heartbeat ok"
];

let allLogs = [];
for (let i = 0; i < 5; i++) {
  allLogs = allLogs.concat(baseLines);
}

const originalContent = allLogs.join("\n");
const compressor = new LogCompressor(10);
const { header, compressed } = compressor.compress(allLogs);

const compressedLogs = compressed.join("\n");
const stats = {
  originalChars: originalContent.length,
  compressedChars: compressedLogs.length + header.length,
  savings: (((originalContent.length - (compressedLogs.length + header.length)) / originalContent.length) * 100).toFixed(2)
};

console.log(header);
console.log("COMPRESSED LOGS:");
console.log(compressedLogs);
console.log("\nSTATS:");
console.log(`Original: ${stats.originalChars} chars`);
console.log(`Compressed: ${stats.compressedChars} chars`);
console.log(`Savings: ${stats.savings}%`);
