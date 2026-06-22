FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi==0.116.1 uvicorn==0.35.0 pydantic==2.11.7
COPY gateway_service.py ./
EXPOSE 8092
CMD ["uvicorn", "gateway_service:app", "--host", "0.0.0.0", "--port", "8092"]
