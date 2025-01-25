# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg and unzip
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg unzip wget && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download and extract Quran MP3 files
RUN mkdir -p /app/quran_mp3s && \
    wget -O /app/quran.zip "https://farhadmotiwala.sharepoint.com/:u:/s/Quranmp3info/Ecib6kPod6FPnRLoigex0ygBVn_xlhatskd--WPWrT6hdg?e=0qWZ5G&download=1" && \
    unzip /app/quran.zip -d /app/quran_mp3s && \
    rm /app/quran.zip

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "bot.py"] 