FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8200

CMD ["uvicorn", "mail_server:app", "--host", "0.0.0.0", "--port", "8200"]
