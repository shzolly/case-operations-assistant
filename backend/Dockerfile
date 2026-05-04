FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN addgroup --system app && adduser --system --ingroup app app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY knowledge ./knowledge
COPY scripts ./scripts
COPY run_local_server.py ./run_local_server.py

USER app

EXPOSE 8000
CMD ["uvicorn", "backend.app.api:app", "--host", "0.0.0.0", "--port", "8000"]

