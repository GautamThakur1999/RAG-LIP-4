# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Copy only the deployment requirements first to leverage Docker cache
COPY requirements-deploy.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy the rest of the application code
# (Assuming .dockerignore is set up to ignore .venv, chroma_db, frontend, etc.)
COPY . .

# Default port variable (Railway will override this with its own dynamic $PORT)
ENV PORT=8000

# Expose the port
EXPOSE $PORT

# Start the FastAPI application
CMD uvicorn app.api:app --host 0.0.0.0 --port $PORT
