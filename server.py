import ast
import json
import re
from typing import Dict, List, Tuple, Literal, Annotated, Any
from fastmcp import FastMCP

DEFAULT_MIN_LEN = 10

class LogCompressor:
    def __init__(self, min_len: int = DEFAULT_MIN_LEN, mode: Literal["lossless", "semantic"] = "semantic"):
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

        line = self.normalize_dynamic_values(line)
        line = self.normalize_structured_context(line)
        return line

    def normalize_dynamic_values(self, line: str) -> str:
        """Collapse high-cardinality values that rarely help root-cause analysis."""
        line = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', line, flags=re.I)
        line = re.sub(r'\b[0-9a-f]{16,}\b', '<HEX>', line, flags=re.I)
        line = re.sub(r'\bprocess \[\d+\]', 'process [<PID>]', line)
        line = re.sub(r'\bin \d+(?:\.\d+)? seconds\b', 'in <DURATION> seconds', line)
        line = re.sub(r'\bapi-version=\d{4}-\d{2}-\d{2}(?:-[A-Za-z0-9-]+)?', 'api-version=<API_VERSION>', line)
        line = re.sub(r'\bikey=[A-Za-z0-9-]+', 'ikey=<KEY>', line)
        return line

    def normalize_structured_context(self, line: str) -> str:
        if " | " not in line:
            return line

        prefix, suffix = line.rsplit(" | ", 1)
        suffix = suffix.strip()
        parsed: Any

        try:
            if suffix.startswith("{") and suffix.endswith("}"):
                parsed = ast.literal_eval(suffix)
            else:
                parsed = json.loads(suffix)
        except (ValueError, SyntaxError, json.JSONDecodeError):
            return line

        if not isinstance(parsed, dict):
            return line

        common_keys = {"taskName", "trace_id", "span_id"}
        if not common_keys.intersection(parsed):
            return line

        task = parsed.get("taskName")
        trace = parsed.get("trace_id")
        span = parsed.get("span_id")
        extras = {k: v for k, v in parsed.items() if k not in common_keys and v is not None}

        if task is None and trace is None and span is None and not extras:
            return f"{prefix} | <CTX:none>"

        parts: List[str] = []
        if task is not None:
            parts.append(f"task={task}")
        if trace is not None:
            parts.append("trace=<TRACE>")
        if span is not None:
            parts.append("span=<SPAN>")
        for key in sorted(extras):
            value = extras[key]
            if isinstance(value, str) and len(value) > 32:
                value = "<STR>"
            parts.append(f"{key}={value}")

        return f"{prefix} | <CTX:{','.join(parts) or 'none'}>"

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

        # 2. Lossless timestamp prefix discovery. The exact timestamp remains
        # reconstructable as dictionary key + remaining minute/second fragment.
        if self.mode == "lossless":
            self.add_lossless_timestamp_prefixes(normalized_lines)

        # 3. Boundary-safe segment discovery. Avoid arbitrary n-grams because
        # they create unreadable dictionary entries from the middle of URLs/loggers.
        fragment_counts: Dict[str, int] = {}
        for line in normalized_lines:
            if line in self.reverse_dict:
                continue

            for phrase in self.extract_boundary_phrases(line):
                fragment_counts[phrase] = fragment_counts.get(phrase, 0) + 1

        # Add frequent phrases to dictionary
        sorted_phrases = [
            (phrase, freq) for phrase, freq in fragment_counts.items()
            if (
                freq >= 2
                and len(phrase) >= 15
                and (freq * (len(phrase) - 3) - (len(phrase) + 5)) > 15
            )
        ]
        sorted_phrases.sort(key=lambda item: len(item[0]), reverse=True)

        for phrase, _ in sorted_phrases:
            if phrase not in self.reverse_dict:
                key = self.get_next_key()
                self.dictionary[key] = phrase
                self.reverse_dict[phrase] = key

        # 4. Final Pass - Replace with dictionary keys
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

    def add_lossless_timestamp_prefixes(self, lines: List[str]) -> None:
        candidates: Dict[str, int] = {}

        for line in lines:
            for prefix in self.extract_timestamp_prefixes(line):
                candidates[prefix] = candidates.get(prefix, 0) + 1

        sorted_prefixes = [
            (prefix, freq)
            for prefix, freq in candidates.items()
            if (
                freq >= 2
                and len(prefix) >= 15
                and (freq * (len(prefix) - 3) - (len(prefix) + 5)) > 15
            )
        ]
        sorted_prefixes.sort(key=lambda item: len(item[0]), reverse=True)

        for prefix, _ in sorted_prefixes:
            if prefix not in self.reverse_dict and not self.is_covered_by_existing_pattern(prefix):
                key = self.get_next_key()
                self.dictionary[key] = prefix
                self.reverse_dict[prefix] = key

    def extract_timestamp_prefixes(self, line: str) -> List[str]:
        candidates: List[str] = []

        # 2026-05-19 14:25:56 / 2026-05-19T14:25:56.123Z
        for match in re.finditer(r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:', line):
            candidates.append(match.group(0))

        # 2026-05-26 20:59:01.123 CEST -> date + hour prefix is still exact.
        for match in re.finditer(r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:', line):
            candidates.append(match.group(0))

        # 26/May/2026:20:59:01 +0200
        for match in re.finditer(r'\b\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:', line):
            candidates.append(match.group(0))

        # May 26 20:59:01
        for match in re.finditer(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:', line):
            candidates.append(match.group(0))

        # HDFS-style 081109 203518 -> date + hour prefix.
        for match in re.finditer(r'\b\d{6}\s+\d{2}', line):
            candidates.append(match.group(0))

        # Prefer longer prefixes first and dedupe while preserving order.
        seen = set()
        unique = []
        for candidate in sorted(candidates, key=len, reverse=True):
            if candidate not in seen:
                seen.add(candidate)
                unique.append(candidate)
        return unique

    def is_covered_by_existing_pattern(self, phrase: str) -> bool:
        return any(phrase in pattern for pattern in self.reverse_dict)

    def extract_boundary_phrases(self, line: str) -> List[str]:
        phrases: List[str] = []

        # Structured context tails are safe and often repeated on every line.
        if " | " in line:
            tail = " | " + line.rsplit(" | ", 1)[1]
            if len(tail.strip()) >= self.min_len:
                phrases.append(tail)

        # In lossless mode, keep the original timestamp in place but allow the
        # repeated logger/message tail to be dictionary-compressed.
        if self.mode == "lossless":
            match = re.match(r'^\[[^\]]+? - (.+)$', line)
            if match:
                header_tail = match.group(1)
                if len(header_tail.strip()) >= self.min_len:
                    phrases.append(header_tail)

        # Repeated message bodies after the logger header.
        match = re.match(r'^\[(?:<TS>|[^\]]+?) - [^\]]+\]\s+(.*)$', line)
        if match:
            message = match.group(1)
            if len(message.strip()) >= self.min_len:
                phrases.append(message)

        return phrases


# Initialize FastMCP Server
mcp = FastMCP("logsquash")

@mcp.tool()
def squash_logs(
    logs: Annotated[str, "The log content to squash"],
    mode: Annotated[str, "Compression mode. Use 'semantic' for troubleshooting, summarization, and maximum compression. Use 'lossless' for audits, exact event timelines, forensic analysis, or when every original value and line must remain reconstructable."] = "semantic",
    min_len: Annotated[int, "Minimum pattern length. Default 10 is recommended for maximum semantic compression."] = DEFAULT_MIN_LEN,
) -> str:
    """Compresses massive, repetitive log streams to save LLM context tokens.
    
    Use this tool whenever you receive large log datasets (such as build outputs, test logs, 
    web server access logs, database traces, or syslogs) before analyzing or processing them. 
    Compression reduces context token usage by up to 95% while keeping errors and critical 
    diagnostics fully readable and prominent.
    
    Modes:
    - 'semantic' (default): Best for debugging, root-cause analysis, summaries, agent handoffs, and any situation where the goal is to understand what happened with maximum compression. It normalizes noisy values such as timestamps, trace/span metadata, PIDs, API keys, durations, and repeated structured context while keeping errors and important messages readable.
    - 'lossless': Best for audits, compliance, forensic analysis, exact timing analysis, reproducing event order, or comparing original values. It avoids semantic normalization so timestamps, IDs, metadata fields, line boundaries, and original values remain preserved as much as possible. Repeated timestamp prefixes may be dictionary-compressed, but the exact timestamp remains reconstructable from the dictionary key plus the remaining suffix.
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
        
    compressor = LogCompressor(min_len=min_len, mode=mode)  # type: ignore
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
