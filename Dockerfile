# Use official Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Java JRE for Apache Spark MLlib compatibility and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Streamlit web server port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit web application with dynamic PORT support for Railway / Cloud
CMD ["sh", "-c", "streamlit run app/streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true"]
