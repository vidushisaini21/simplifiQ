# Use the official Microsoft Playwright image which has Python and all browser system dependencies pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
