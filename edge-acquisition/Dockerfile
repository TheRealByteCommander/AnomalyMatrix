FROM python:3.12-slim-bookworm
ARG ANOMALYMATRIX_VERSION=1.0.0
ENV ANOMALYMATRIX_VERSION=$ANOMALYMATRIX_VERSION
WORKDIR /app

# Aravis (open GigE Vision) via GObject introspection. PyGObject 3.48 is the last
# line that matches Bookworm's libgirepository-1.0; a vendor GenTL .cti is optional.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        pkg-config \
        python3-dev \
        libcairo2 \
        libcairo2-dev \
        libgirepository-1.0-1 \
        libgirepository1.0-dev \
        gir1.2-glib-2.0 \
        gir1.2-aravis-0.8 \
        libaravis-0.8-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt "PyGObject==3.48.2" \
    && apt-get purge -y --auto-remove gcc pkg-config python3-dev libcairo2-dev libgirepository1.0-dev \
    && apt-get update && apt-get install -y --no-install-recommends \
        libcairo2 \
        libgirepository-1.0-1 \
        gir1.2-glib-2.0 \
        gir1.2-aravis-0.8 \
        libaravis-0.8-0 \
    && rm -rf /var/lib/apt/lists/*

COPY service.py service_auth.py camera_drivers.py camera_discover.py gige_backend.py ./
EXPOSE 8091
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8091"]
