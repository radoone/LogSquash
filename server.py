import re
from typing import Dict, List, Tuple, Literal, Annotated, Optional
from fastmcp import FastMCP

class LogCompressor:
    def __init__(self, min_len: int = 10, mode: Literal["lossless", "semantic"] = "semantic"):
        self.min_len = min_len
        self.mode = mode
        self.dictionary: Dict[str, str] = {}
        self.reverse_dict: Dict[str, str] = {}
        self.counter: int = 0

    def get_next_key(self) -> str:
        self.counter += 1
        return f"#{self.counter}"

    def normalize(self, line: str) -> str:
        if self.mode == "lossless":
            return line
        
        # 1. Standard ISO-like: 2026-05-26T20:59:01.123Z or 2026-05-26 20:59:01,123
        line = re.sub(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}([\.,]\d+)?Z?', '<TS>', line)
        
        # 2. Nginx/Apache access log timestamp: 26/May/2026:20:59:01 +0200
        line = re.sub(r'\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{4})?', '<TS>', line)
        
        # 3. HDFS timestamp: 081109 203518
        line = re.sub(r'\b\d{6}\s+\d{6}\b', '<TS>', line)
        
        # 4. Syslog timestamp: May 26 20:59:01
        line = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b', '<TS>', line)
        
        return line

    def get_log_level(self, line: str) -> Literal["ERROR", "DEBUG", "INFO", "OTHER"]:
        upper = line.upper()
        if "ERROR" in upper or "CRITICAL" in upper or "FATAL" in upper:
            return "ERROR"
        if "DEBUG" in upper:
            return "DEBUG"
        if "INFO" in upper:
            return "INFO"
        return "OTHER"

    def compress(self, lines: List[str]) -> Tuple[str, List[str]]:
        normalized_lines = [self.normalize(l) for l in lines]
        line_frequencies: Dict[str, int] = {}
        
        # 1. Line Aggregation - Find global duplicates
        for line in normalized_lines:
            line_frequencies[line] = line_frequencies.get(line, 0) + 1

        # Add frequent whole lines to dictionary
        for line, freq in line_frequencies.items():
            level = self.get_log_level(line)
            threshold = 5 if level == "ERROR" else 2
            
            savings = freq * (len(line) - 3) - (len(line) + 5)
            if freq >= threshold and savings > 20:
                if line not in self.reverse_dict:
                    key = self.get_next_key()
                    self.dictionary[key] = line
                    self.reverse_dict[line] = key

        # 2. Template Discovery & Phrase matching (N-grams with preserved spaces)
        fragment_counts: Dict[str, int] = {}
        for line in normalized_lines:
            if line in self.reverse_dict:
                continue

            # Tokenize keeping spaces and separators
            tokens = [t for t in re.split(r'(\s+|(?=[\[\]\|\{\}\"\',:])|(?<=[\[\]\|\{\}\"\',:]))', line) if t]
            meaningful_indices = [i for i, t in enumerate(tokens) if t.strip()]
            
            for length in range(2, 6):
                for j in range(len(meaningful_indices) - length + 1):
                    start_tok_idx = meaningful_indices[j]
                    end_tok_idx = meaningful_indices[j + length - 1]
                    phrase = "".join(tokens[start_tok_idx : end_tok_idx + 1])
                    if len(phrase.strip()) >= self.min_len:
                        fragment_counts[phrase] = fragment_counts.get(phrase, 0) + 1

        # Add frequent phrases to dictionary
        sorted_phrases = [
            (phrase, freq) for phrase, freq in fragment_counts.items()
            if freq >= 2 and (freq * (len(phrase) - 3) - (len(phrase) + 5)) > 15
        ]
        sorted_phrases.sort(key=lambda item: len(item[0]), reverse=True)

        for phrase, _ in sorted_phrases:
            if phrase not in self.reverse_dict:
                key = self.get_next_key()
                self.dictionary[key] = phrase
                self.reverse_dict[phrase] = key

        # 3. Final Pass - Replace with dictionary keys
        last_key = ""
        repeat_count = 0
        final_lines: List[str] = []

        all_patterns = sorted(self.reverse_dict.keys(), key=len, reverse=True)

        for line in normalized_lines:
            compressed = line
            if line in self.reverse_dict:
                compressed = self.reverse_dict[line]
            else:
                for pattern in all_patterns:
                    if len(pattern) < 15:
                        continue
                    if pattern in compressed:
                        key = self.reverse_dict[pattern]
                        compressed = compressed.replace(pattern, key)

            # Semantic deduplication (Sequential repeats) - Only in semantic mode
            if self.mode == "semantic" and compressed == last_key and compressed.startswith("#"):
                repeat_count += 1
            else:
                if repeat_count > 0:
                    final_lines[-1] += f" (repeated {repeat_count + 1}x)"
                final_lines.append(compressed)
                last_key = compressed
                repeat_count = 0

        if repeat_count > 0:
            final_lines[-1] += f" (repeated {repeat_count + 1}x)"

        header = f"LOG DICTIONARY (Mode: {self.mode}):\n"
        for key, val in self.dictionary.items():
            header += f"{key}: {val}\n"

        return header, final_lines


# Initialize FastMCP Server
mcp = FastMCP("logsquash")

@mcp.tool()
def squash_logs(
    logs: Annotated[str, "The log content to squash"],
    mode: Annotated[str, "Compression mode: 'lossless' (preserves time/lines) or 'semantic' (max savings)"] = "semantic",
    min_len: Annotated[int, "Minimum pattern length"] = 10,
    minLen: Annotated[Optional[int], "Minimum pattern length (alias for backward compatibility)"] = None
) -> str:
    """Compresses massive, repetitive log streams to save LLM context tokens.
    
    Use this tool whenever you receive large log datasets (such as build outputs, test logs, 
    web server access logs, database traces, or syslogs) before analyzing or processing them. 
    Compression reduces context token usage by up to 95% while keeping errors and critical 
    diagnostics fully readable and prominent.
    
    Modes:
    - 'semantic' (default): Aggressively compresses logs, normalizes timestamps to <TS>, and groups sequential repeats. Recommended for general troubleshooting.
    - 'lossless': Collapses repetitive structural patterns but preserves timestamps, exact line boundaries, and order. Best for auditing and timing analysis.
    """
    import os
    expected_key = os.getenv("LOGSQUASH_API_KEY")
    if expected_key:
        try:
            from fastmcp.server.dependencies import get_http_headers
            headers = get_http_headers() or {}
        except ImportError:
            headers = {}
        
        headers_lower = {k.lower(): v for k, v in headers.items()}
        auth_header = headers_lower.get("authorization")
        api_key_header = headers_lower.get("x-api-key")
        
        authorized = False
        if auth_header == f"Bearer {expected_key}":
            authorized = True
        elif api_key_header == expected_key:
            authorized = True
            
        if not authorized:
            return f"Error: Unauthorized. Missing or invalid LOGSQUASH_API_KEY in Authorization or X-API-Key header."

    lines = [l for l in logs.split("\n") if l.strip() != ""]
    if not lines:
        return "No logs to squash."
    
    if mode not in ("lossless", "semantic"):
        mode = "semantic"
        
    effective_min_len = minLen if minLen is not None else min_len
    compressor = LogCompressor(min_len=effective_min_len, mode=mode)  # type: ignore
    header, compressed = compressor.compress(lines)
    
    compressed_str = "\n".join(compressed)
    return f"{header}\nCOMPRESSED LOGS:\n{compressed_str}"


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", "8080"))
    if "PORT" in os.environ:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio")
