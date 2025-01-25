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
    wget -O /app/quran.zip "https://drive.usercontent.google.com/download?id=1rea9cx4ufxBbpUpW9NyO8qT2KhsWhIS3&export=download&authuser=0&confirm=t&uuid=535d6325-2354-43a8-9169-35bf82c777cc&at=AIrpjvNZ_lPBqXc8riWzx6cIRbBl%3A1737823934983" && \
    unzip /app/quran.zip -d /app/quran_mp3s && \
    rm /app/quran.zip && \
    echo "MP3 files downloaded:" && \
    ls -lh /app/quran_mp3s && \
    echo "Total files:" && \
    find /app/quran_mp3s -type f | wc -l

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "bot.py"] 