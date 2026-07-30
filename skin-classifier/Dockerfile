FROM python:3.12-slim

WORKDIR /app
ENV PYTHONIOENCODING=utf-8

COPY skin-classifier/requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt fastapi uvicorn[standard]

COPY skin-classifier/ .

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
