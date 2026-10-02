FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    PORT=7860

EXPOSE 7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize DB schema and funds table
RUN python scripts/initialize.py

# Launch Telegram bot daemon with 24/7 scheduler
CMD ["python", "scripts/run_telegram_bot.py"]
