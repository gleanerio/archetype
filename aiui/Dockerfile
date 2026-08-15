FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ODIS_EXPLORER_HOST=0.0.0.0 \
    ODIS_EXPLORER_PORT=8765

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY odis_explorer ./odis_explorer
COPY odis-search.py odis-explorer.py ./

RUN useradd --create-home --uid 10001 explorer \
    && chown -R explorer:explorer /app
USER explorer

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/', timeout=4)"

CMD ["python", "-m", "odis_explorer", "--host", "0.0.0.0", "--port", "8765"]
