FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY service.py service_auth.py camera_drivers.py ./
EXPOSE 8091
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8091"]
