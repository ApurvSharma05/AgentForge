# Multi-stage/lightweight Dockerfile for AgentForge
FROM python:3.11-slim

# Prevent Python from writing .pyc files to disc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install curated application dependencies
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

# Copy application source code (excluding secrets via .dockerignore)
COPY *.py ./
COPY README.md ./

# Default Streamlit web UI port
EXPOSE 8501

# Run Streamlit UI
# Note: Inject SERP_API_KEY and GROQ_API_KEY at container runtime:
# docker run -e SERP_API_KEY=... -e GROQ_API_KEY=... -p 8501:8501 agentforge
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
