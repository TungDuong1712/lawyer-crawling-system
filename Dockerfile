FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and set timeout
RUN pip install --upgrade pip
RUN pip config set global.timeout 1000
RUN pip config set global.retries 5

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in stages to avoid timeout
RUN pip install --no-cache-dir Django==4.2.7
RUN pip install --no-cache-dir djangorestframework==3.14.0
RUN pip install --no-cache-dir django-cors-headers==4.3.1
RUN pip install --no-cache-dir psycopg2-binary==2.9.7
RUN pip install --no-cache-dir redis==5.0.1
RUN pip install --no-cache-dir celery==5.3.4
RUN pip install --no-cache-dir requests==2.31.0
RUN pip install --no-cache-dir beautifulsoup4==4.12.2
RUN pip install --no-cache-dir pandas==2.1.3
RUN pip install --no-cache-dir lxml==4.9.3
RUN pip install --no-cache-dir fake-useragent==1.4.0
RUN pip install --no-cache-dir python-dotenv==1.0.0
RUN pip install --no-cache-dir gunicorn==21.2.0
RUN pip install --no-cache-dir whitenoise==6.6.0
RUN pip install --no-cache-dir django-filter==23.3

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/static /app/media /app/logs
RUN chmod 755 /app/logs

# Create non-root user
RUN useradd -m -u 1000 crawler && chown -R crawler:crawler /app
USER crawler

# Expose port
EXPOSE 8000

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "lawyers_project.wsgi:application"]