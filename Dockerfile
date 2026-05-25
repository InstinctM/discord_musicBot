FROM python:3.12

# Set working directory
WORKDIR /opt

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y ffmpeg

# Set a volume for the application code
VOLUME ["/opt"]

EXPOSE 8080

# Start the bot
CMD ["python", "main.py"]