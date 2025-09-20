# Stage 1: Use the official Python image as a base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the file that lists our Python dependencies
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application's code into the container
COPY . .

# Command to run when the container starts
# This will execute our main application loop
CMD ["python", "main.py"]
