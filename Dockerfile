# NAQ
# A lightweight, containerized AI Natural Language -> SQL Engine

# Use official Python lightweight image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire source code into the container
COPY . .

# Install NAQ as a global command
RUN pip install --no-cache-dir .

# By default, running the container will start the NAQ REPL
# Need to use -it (interactive tty) when running docker
ENTRYPOINT ["NAQ"]
