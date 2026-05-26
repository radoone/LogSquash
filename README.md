# LogSquash 🪵🗜️ v3.3.1 (Python FastMCP Version)

Advanced semantic log compression built with **FastMCP** for AI agents (Gemini, Claude, Cursor) and developer workflows. Squashes massive, repetitive production logs into compact, structure-preserving representations, allowing AI models to analyze **10x more history** within their token contexts.

---

## Features 🚀

- **Semantic Priority**: Critical error logs (`ERROR`, `FATAL`, `CRITICAL`) remain fully readable and inline, while repetitive debug/info logs are squashed into the dictionary.
- **Space-Preserving Template Discovery**: Identifies repetitive structural phrases (N-grams) while preserving whitespaces and delimiters for maximum replacement accuracy.
- **Multi-Format Timestamp Normalization**: Automatically normalizes diverse production log timestamp formats (ISO-8601, Nginx/Apache, HDFS, Syslog) to `<TS>` in `semantic` mode.
- **Multi-Mode Compression**:
  - `semantic` (default): Max savings (up to **95%+**), replaces timestamps with `<TS>`, groups repeated lines, collapses structural redundancy.
  - `lossless`: Full precision (~40-50% savings), preserves exact timing and all line boundaries.

---

## Log Compression Example (Semantic Mode) 🧠

Below is an example showing how structured JSON microservice logs containing debug info and a critical server crash are processed by LogSquash.

### 📄 Original Logs
```json
{"timestamp":"2026-05-26T20:59:01.001Z","level":"INFO","service":"auth-service","traceId":"tr-921820","message":"User verification started","userId":"user-8291"}
{"timestamp":"2026-05-26T20:59:01.005Z","level":"DEBUG","service":"auth-service","traceId":"tr-921820","message":"Checking cache for user","userId":"user-8291"}
{"timestamp":"2026-05-26T20:59:01.010Z","level":"INFO","service":"auth-service","traceId":"tr-921820","message":"Cache miss. Querying DB","userId":"user-8291"}
{"timestamp":"2026-05-26T20:59:01.012Z","level":"ERROR","service":"auth-service","traceId":"tr-921820","message":"Failed to connect to database at db.internal:5432","error":"Connection timeout"}
{"timestamp":"2026-05-26T20:59:02.001Z","level":"INFO","service":"auth-service","traceId":"tr-921821","message":"User verification started","userId":"user-8292"}
{"timestamp":"2026-05-26T20:59:02.003Z","level":"DEBUG","service":"auth-service","traceId":"tr-921821","message":"Checking cache for user","userId":"user-8292"}
{"timestamp":"2026-05-26T20:59:02.004Z","level":"INFO","service":"auth-service","traceId":"tr-921821","message":"Cache hit. Verification success","userId":"user-8292"}
{"timestamp":"2026-05-26T20:59:03.001Z","level":"FATAL","service":"gateway-service","traceId":"tr-921822","message":"System panic: nil pointer dereference at auth.go:124","stack_trace":"runtime.panic(...) auth.verifyUser(...)"}
```

### 🗜️ Compressed Output (Sent to LLM)
```text
LOG DICTIONARY (Mode: semantic):
#1: :"User verification started
#4: service":"auth-service
#6: traceId":"tr-921820
#8: traceId":"tr-921821
#10: userId":"user-8291
#11: userId":"user-8292
#12: timestamp":"<TS>

COMPRESSED LOGS:
{"#12","level":"INFO","#4","#6","message"#1","#10"}
{"#12","level":"DEBUG","#4","#6","message":"Checking cache for user","#10"}
{"#12","level":"INFO","#4","#6","message":"Cache miss. Querying DB","#10"}
{"#12","level":"ERROR","#4","#6","message":"Failed to connect to database at db.internal:5432","error":"Connection timeout"}
{"#12","level":"INFO","#4","#8","message"#1","#11"}
{"#12","level":"DEBUG","#4","#8","message":"Checking cache for user","#11"}
{"#12","level":"INFO","#4","#8","message":"Cache hit. Verification success","#11"}
{"#12","level":"FATAL","service":"gateway-service","traceId":"tr-921822","message":"System panic: nil pointer dereference at auth.go:124","stack_trace":"runtime.panic(...) auth.verifyUser(...)"}
```
*Notice how the key structural patterns like `timestamp:"<TS>"` and `service: "auth-service"` are replaced by short hashes (`#12`, `#4`), while unique, critical diagnostic entries like **`ERROR (Failed to connect...)`** and **`FATAL (System panic...)`** remain completely legible inline.*

---

## Performance & Compression Benchmarks 📊

We benchmarked the Python FastMCP LogSquash implementation under real-world conditions where each log entry contains a **unique timestamp** but logs follow standard templates (tested with 200 entries per format):

| Log File Format | Mode | Original Size | Compressed Size | Savings % | Execution Time |
|---|---|---|---|---|---|
| **HDFS Logs** | `semantic` | 25,599 ch | 1,365 ch | **94.67%** | 1.49 ms |
| **Linux Syslog** | `semantic` | 23,292 ch | 1,289 ch | **94.47%** | 1.29 ms |
| **Microservice JSON** | `semantic` | 34,924 ch | 1,901 ch | **94.56%** | 1.54 ms |
| **Nginx Access** | `semantic` | 28,469 ch | 2,361 ch | **91.71%** | 1.52 ms |
| **PostgreSQL LOG** | `semantic` | 27,779 ch | 1,376 ch | **95.05%** | 1.27 ms |

*In `lossless` mode, LogSquash achieves **~40-50% savings** on structured log formats by collapsing repetitive templates without normalizing timestamps.*

---

## Installation & Local Execution 💻

1. Create a virtual environment and install the dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the local benchmark test suite:
   ```bash
   python3 run_logsquash_tests.py
   ```

3. Run the FastMCP server locally in development mode:
   ```bash
   fastmcp dev server.py:mcp
   ```

---



## Deployment on Google Cloud Run ☁️

LogSquash is ready to be deployed to **Google Cloud Run** using the provided `Dockerfile`. Under Cloud Run, the server automatically detects the `PORT` environment variable and runs using the recommended `"streamable-http"` transport.

### Steps to Deploy:
1. Make sure you have the [Google Cloud SDK](https://cloud.google.com/sdk) installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Deploy the service directly from the source directory, setting your shared API key via the `LOGSQUASH_API_KEY` environment variable:
   ```bash
   gcloud run deploy logsquash \
     --source . \
     --platform managed \
     --region europe-west3 \
     --set-env-vars="LOGSQUASH_API_KEY=YOUR_SECRET_KEY" \
     --allow-unauthenticated
   ```
   *Note: Using `--allow-unauthenticated` makes the HTTP endpoint publicly accessible, but the Python application code itself will block any requests that do not provide the correct key.*

### How Clients Connect using the API Key:

#### In Python scripts:
To prevent header processing/stripping issues on intermediate gateways, pass the key as a custom `X-API-Key` header:
```python
from fastmcp import Client
from fastmcp.client.transports.http import StreamableHttpTransport

transport = StreamableHttpTransport(
    "https://YOUR_SERVICE_URL/mcp",
    headers={"X-API-Key": "YOUR_SECRET_KEY"}
)
client = Client(transport)

async with client:
    res = await client.call_tool("squash_logs", {"logs": "...log data..."})
```

#### In Cursor:
1. Open **Cursor Settings > Features > MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in:
   - **Name**: `logsquash`
   - **Type**: `SSE` (or `HTTP` depending on your version)
   - **URL**: `https://YOUR_SERVICE_URL/mcp`
4. Add Header:
   - **Key**: `X-API-Key`
   - **Value**: `YOUR_SECRET_KEY`

#### In Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "logsquash": {
      "url": "https://YOUR_SERVICE_URL/mcp",
      "headers": {
        "X-API-Key": "YOUR_SECRET_KEY"
      }
    }
  }
}
```

