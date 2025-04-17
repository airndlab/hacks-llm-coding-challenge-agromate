FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir sqlmodel aiosqlite

# Copy application code
COPY . .

# Command to run the application
CMD ["uvicorn", "agroapp.main:app", "--host", "0.0.0.0", "--port", "8080"] 