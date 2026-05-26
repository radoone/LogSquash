FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and logs
COPY server.py .

# Expose port (Cloud Run sets PORT environment variable, defaults to 8080)
EXPOSE 8080

# Start server
CMD ["python", "server.py"]
