FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
RUN useradd -r -s /bin/false appuser
USER appuser
CMD ["python", "app.py"]
