FROM python:3.12-slim
ARG ANOMALYMATRIX_VERSION=1.0.0
ENV ANOMALYMATRIX_VERSION=$ANOMALYMATRIX_VERSION
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY service.py service_auth.py camera_drivers.py camera_discover.py ./
EXPOSE 8091
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8091"]
