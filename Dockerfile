FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY . .
RUN pip install --no-cache-dir .
ENTRYPOINT ["python", "-m", "qgis_layer_diff"]
LABEL org.opencontainers.image.title="qgis-layer-diff" \
      org.opencontainers.image.source="https://github.com/tabibhasan/qgis_layer_diff" \
      org.opencontainers.image.licenses="GPL-2.0"
