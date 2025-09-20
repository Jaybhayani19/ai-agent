# Start from the official Python 3.11 slim image
FROM python:3.11-slim

# Pre-install pytest so we don't need to do it at runtime
RUN pip install pytest pytest-mock

# Set the working directory for our app
WORKDIR /app

# Create a non-root user with a UID/GID that we will pass in during the build
# This is the key to solving the permission issues
ARG UID=1000
ARG GID=1000
RUN groupadd --gid $GID appgroup && \
    useradd --uid $UID --gid $GID --shell /bin/bash --create-home appuser

# Switch the default user for the container to our new user
USER appuser
