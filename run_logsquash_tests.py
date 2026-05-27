import os
import re
import time
from typing import Dict, List, Tuple, Literal
from server import DEFAULT_MIN_LEN, LogCompressor

TEST_LOGS_DIR = "data/test_logs"

def make_unique_timestamps(filename: str, lines: List[str]) -> List[str]:
    processed_lines = []
    
    for i, line in enumerate(lines):
        minute = (i // 60) % 60
        second = i % 60
        
        if filename == "nginx_access.log":
            timestamp = f"26/May/2026:20:{minute:02d}:{second:02d} +0200"
            line = re.sub(r'\[\d{2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{4})?\]', f"[{timestamp}]", line)
            
        elif filename == "hdfs.log":
            timestamp = f"081109 20{minute:02d}{second:02d}"
            line = re.sub(r'^\d{6}\s+\d{6}', timestamp, line)
            
        elif filename == "microservice_json.log":
            timestamp = f"2026-05-26T20:{minute:02d}:{second:02d}.000Z"
            line = re.sub(r'"timestamp":"[^"]+"', f'"timestamp":"{timestamp}"', line)
            
        elif filename == "linux_secure.log":
            timestamp = f"May 26 20:{minute:02d}:{second:02d}"
            line = re.sub(r'^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}', timestamp, line)
            
        elif filename == "postgres.log":
            timestamp = f"2026-05-26 20:{minute:02d}:{second:02d}.{i:03d} CEST"
            line = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+[A-Z]{3,4}', timestamp, line)
            
        elif filename == "python_app_observability.log":
            timestamp = f"2026-05-19 14:{minute:02d}:{second:02d}"
            line = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', timestamp, line, count=1)
            
        processed_lines.append(line)
        
    return processed_lines

def run_tests():
    print("# Production LogSquash Performance Statistics (200 unique-timestamp entries each)\n")
    print("| Log File | Mode | Original Size | Compressed Size | Savings % | Time (ms) |")
    print("|---|---|---|---|---|---|")
    
    log_files = sorted(os.listdir(TEST_LOGS_DIR))
    
    for filename in log_files:
        if not filename.endswith(".log"):
            continue
            
        filepath = os.path.join(TEST_LOGS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            logs_content = f.read()
            
        base_lines = [l for l in logs_content.split("\n") if l.strip() != ""]
        if not base_lines:
            continue
            
        replicated_lines = []
        while len(replicated_lines) < 200:
            replicated_lines.extend(base_lines)
        replicated_lines = replicated_lines[:200]
        
        test_lines = make_unique_timestamps(filename, replicated_lines)
        test_content = "\n".join(test_lines)
        orig_chars = len(test_content)
        
        # Run semantic mode
        start = time.perf_counter()
        compressor = LogCompressor(min_len=DEFAULT_MIN_LEN, mode="semantic")
        h, c = compressor.compress(test_lines)
        t = (time.perf_counter() - start) * 1000
        comp_size = len("\n".join(c)) + len(h)
        savings = (orig_chars - comp_size) / orig_chars * 100
        print(f"| `{filename}` | semantic | {orig_chars} ch | {comp_size} ch | {savings:.2f}% | {t:.2f} ms |")
        
        # Run lossless mode
        start = time.perf_counter()
        compressor_loss = LogCompressor(min_len=DEFAULT_MIN_LEN, mode="lossless")
        h_loss, c_loss = compressor_loss.compress(test_lines)
        t_loss = (time.perf_counter() - start) * 1000
        comp_size_loss = len("\n".join(c_loss)) + len(h_loss)
        savings_loss = (orig_chars - comp_size_loss) / orig_chars * 100
        print(f"| `{filename}` | lossless | {orig_chars} ch | {comp_size_loss} ch | {savings_loss:.2f}% | {t_loss:.2f} ms |")
        
        print("| | | | | | |") # Row separator

if __name__ == "__main__":
    run_tests()
