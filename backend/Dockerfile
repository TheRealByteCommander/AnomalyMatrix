FROM python:3.14-slim

ARG ANOMALYMATRIX_VERSION=1.0.0
ENV ANOMALYMATRIX_VERSION=$ANOMALYMATRIX_VERSION

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY contracts ./contracts
COPY VERSION ./VERSION

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
