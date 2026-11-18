FROM python:3.12-alpine
WORKDIR /app
RUN pip install --timeout=100 --retries=5 flask
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
