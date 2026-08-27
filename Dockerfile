# ADOFAI Offset Analyzer — Discord bot container
# Build:  docker build -t aoabot .
# Run:    docker run --rm -v "$(pwd)/config.yml:/app/config.yml" aoabot

# Match the dev environment (Python 3.13); slim keeps the image small.
# No build tools are needed — matplotlib/numpy/pycryptodome all ship wheels.
FROM python:3.13-slim

ENV MPLBACKEND=Agg \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first so rebuilds reuse the layer cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app (venv/, __pycache__/, config.yml etc. are excluded via .dockerignore).
COPY . .

# Run as an unprivileged user. /app is chowned so the bot can auto-generate
# config.yml on first run (it is a small file, created at /app/config.yml).
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

# Bot state that should live outside the image (token never baked into the build):
#   - config.yml  → mount a host copy with your real token
#   - data/ logs/ → persistent output if you add any
VOLUME ["/app/config.yml", "/app/data", "/app/logs"]

CMD ["python", "-m", "main"]
