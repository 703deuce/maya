# Multi-stage Dockerfile for Maya1 RunPod Serverless Endpoint
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    git-lfs \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set up Python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Install git-lfs and initialize
RUN git lfs install

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy handler and other application files
COPY handler.py .

# Create directory for model cache (optional, for local testing)
RUN mkdir -p /app/models

# Expose port (RunPod uses port 8000 by default)
EXPOSE 8000

# Set entry point
CMD ["python", "handler.py"]

