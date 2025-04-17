FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY agroapp/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir sqlmodel aiosqlite

# Copy application code without folders hierarchy
COPY agroapp/*.py agroapp/__init__.py ./
COPY agroapp/pipelines ./pipelines/

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 