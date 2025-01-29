FROM python:3.12.0
ENV APP_PORT=8000
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config  /root/.aws/config
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY origin_service.py .
COPY utile ./utile
CMD uvicorn origin_service:app --host 0.0.0.0 --port $APP_PORT