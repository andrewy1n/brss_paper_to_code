FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy and install main requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install brss_paper_to_code requirements
COPY brss_paper_to_code/requirements.txt ./brss_requirements.txt
RUN pip install --no-cache-dir -r brss_requirements.txt

# Expose port for FastAPI server
EXPOSE 8000

# Default command
CMD ["bash"] 