FROM python:3.11-slim
WORKDIR /app
COPY opcua-gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY opcua-gateway/gateway_service.py opcua-gateway/opcua_server.py opcua-gateway/plc_bridge.py opcua-gateway/inspection_client.py opcua-gateway/nodes.py ./
COPY contracts/opcua_nodeset_mapping_v1.json ./opcua_nodeset_mapping_v1.json
EXPOSE 8092 4840
CMD ["uvicorn", "gateway_service:app", "--host", "0.0.0.0", "--port", "8092"]
