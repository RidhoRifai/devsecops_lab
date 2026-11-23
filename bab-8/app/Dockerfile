FROM python:3.11-slim
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip uninstall -y pip setuptools wheel
COPY app.py .
USER app
EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000')"]
CMD ["python", "app.py"]
