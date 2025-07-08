# Use an official Python image as a base
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg2 curl unzip && \
    # Install Chrome
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    # Clean up
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set display port to avoid crash
ENV DISPLAY=:99

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port (if running as a web server)
EXPOSE 8000

# Command to run the FastAPI app (adjust if you use a different entrypoint)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 