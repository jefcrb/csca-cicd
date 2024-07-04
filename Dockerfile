# Use the official Python image from the DockerHub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install the requirements
RUN pip install -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Set the PYTHONPATH
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "run.py"]
