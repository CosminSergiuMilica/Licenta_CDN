FROM python:3.9-slim
ENV APP_PORT=8000
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config  /root/.aws/config
WORKDIR /app
COPY app.py .
COPY requirements.txt .
COPY utile ./utile
RUN pip install -r requirements.txt
EXPOSE 8000
CMD uvicorn app:app --host 0.0.0.0 --port $APP_PORT