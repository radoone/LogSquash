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
        return re.sub(r'\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(,\d+)?Z?', '<TS>', line)

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

        # 2. Template Discovery & Phrase matching (N-grams)
        fragment_counts: Dict[str, int] = {}
        for line in normalized_lines:
            if line in self.reverse_dict:
                continue

            raw_tokens = [
                t for t in re.split(
                    r'(\s+|(?=[\[\]\|\{\}\"\',:])|(?<=[\[\]\|\{\}\"\',:]))',
                    line
                ) if t and t.strip()
            ]
            for length in range(2, 6):
                for i in range(len(raw_tokens) - length + 1):
                    phrase = "".join(raw_tokens[i:i + length])
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
    """Advanced log compression. Choose 'semantic' for max savings or 'lossless' for full precision."""
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
