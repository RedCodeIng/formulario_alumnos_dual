
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for PostgreSQL and building Python packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    libffi-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=America/Mexico_City
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/src/assets/images/logos /app/src/assets/templates /app/src/components /app/src/views /app/src/utils

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 8501 for Streamlit
EXPOSE 8501

# Command to run the application
# Use specific entrypoint for Streamlit with configuration
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableStaticServing=true"]
