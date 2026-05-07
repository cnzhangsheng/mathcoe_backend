FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for weasyprint (pango, gdk-pixbuf) and MySQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Install Python dependencies (includes the app package itself)
RUN pip install --no-cache-dir .

# Create runtime directories
RUN mkdir -p logs storage/exam_papers

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
