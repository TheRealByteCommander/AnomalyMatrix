FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway_service.py opcua_server.py ./
EXPOSE 8092 4840
CMD ["uvicorn", "gateway_service:app", "--host", "0.0.0.0", "--port", "8092"]
