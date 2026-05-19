import fs from 'fs';

class LogCompressor {
  constructor(minLen = 10, minFreq = 2) {
    this.minLen = minLen;
    this.minFreq = minFreq;
    this.dictionary = new Map();
    this.reverseDict = new Map();
    this.counter = 0;
  }

  getNextKey() {
    this.counter++;
    return "#" + this.counter;
  }

  findPatterns(lines) {
    const fragmentCounts = new Map();

    for (const line of lines) {
      let normalized = line.replace(/\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(,\d+)?Z?/g, "<TS>");
      const tokens = normalized.split(/[\s\[\]\|\{\}\"\',:]+/).filter(t => t.length >= this.minLen);
      for (const token of tokens) {
        fragmentCounts.set(token, (fragmentCounts.get(token) || 0) + 1);
      }

      const rawTokens = normalized.split(/(\s+|(?=[\[\]\|\{\}\"\',:]+)|(?<=[\[\]\|\{\}\"\',:]+))/).filter(t => t.trim().length > 0);
      for (let len = 2; len <= 5; len++) {
        for (let i = 0; i <= rawTokens.length - len; i++) {
          const phrase = rawTokens.slice(i, i + len).join("");
          if (phrase.trim().length >= this.minLen) {
            fragmentCounts.set(phrase, (fragmentCounts.get(phrase) || 0) + 1);
          }
        }
      }
    }

    return Array.from(fragmentCounts.entries())
      .filter(([_, freq]) => freq >= this.minFreq)
      .map(([text]) => text)
      .sort((a, b) => b.length - a.length);
  }

  compress(lines) {
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
        const key = this.reverseDict.get(pattern);
        compressed = compressed.split(pattern).join(key);
      }
      return compressed;
    });

    let header = "LOG DICTIONARY:\n";
    this.dictionary.forEach((val, key) => {
      header += key + ": " + val + "\n";
    });

    return { header, compressed: compressedLines };
  }
}

const logs = fs.readFileSync('logs.txt', 'utf8');
const lines = logs.split("\n").filter(l => l.trim() !== "");
const compressor = new LogCompressor(10, 2);
const { header, compressed } = compressor.compress(lines);

const originalCharCount = logs.length;
const compressedOutput = compressed.join("\n");
const dictionaryCharCount = header.length;
const totalCompressedSize = compressedOutput.length + dictionaryCharCount;
const savings = ((originalCharCount - totalCompressedSize) / originalCharCount * 100).toFixed(2);

console.log(header);
console.log("\nCOMPRESSED LOGS:");
console.log(compressedOutput);
console.log("\nCOMPRESSION STATS:");
console.log(`Original characters: ${originalCharCount}`);
console.log(`Compressed characters (including dictionary): ${totalCompressedSize}`);
console.log(`Savings: ${savings}%`);
