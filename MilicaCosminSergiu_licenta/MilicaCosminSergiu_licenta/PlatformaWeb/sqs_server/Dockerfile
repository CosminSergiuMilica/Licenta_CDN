FROM python:3.12.0-slim

WORKDIR /app

COPY requirements.txt .
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config  /root/.aws/config
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8221

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8221"]
