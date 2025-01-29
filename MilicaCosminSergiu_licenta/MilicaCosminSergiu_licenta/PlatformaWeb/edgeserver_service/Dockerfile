FROM python:3.12.0
ENV APP_PORT=8000
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config  /root/.aws/config
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY utile ./utile
CMD uvicorn app:app --host 0.0.0.0 --port $APP_PORT