# Use a lightweight Python base
FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install system deps (if needed for scapy, bleak, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpcap-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app
COPY . .

# Ensure Streamlit runs headlessly
ENV STREAMLIT_SERVER_HEADLESS=true

# Expose Streamlit port
EXPOSE 8501

# Run the dashboard
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]