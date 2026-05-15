# ── Stage 1: Base image ─────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# ── Stage 2: Install system dependencies ────────────────────
# Install Chrome + ChromeDriver for Selenium tests
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tell Selenium where ChromeDriver is
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

# ── Stage 3: Install Python dependencies ────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install test dependencies
RUN pip install --no-cache-dir pytest selenium

# ── Stage 4: Copy application code ──────────────────────────
COPY . .

# Create directory for SQLite database
RUN mkdir -p /app/instance

# ── Stage 5: Expose port & run ───────────────────────────────
EXPOSE 5000

# Initialize DB and start Flask
CMD ["sh", "-c", "python -c 'from app import app, db; \
     app.app_context().push(); db.create_all()' && \
     python app.py"]
