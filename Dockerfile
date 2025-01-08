# Use a base image that supports Selenium and Chromium
FROM python:3.9-slim

# Install necessary system dependencies
RUN apt-get update \
    && apt-get install -y \
    wget \
    ca-certificates \
    curl \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install webdriver-manager
RUN pip install webdriver-manager

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV CHROMIUM_BINARY=/usr/bin/chromium

# Expose the port
EXPOSE 5000

# Command to run the app
CMD ["python", "main.py"]
