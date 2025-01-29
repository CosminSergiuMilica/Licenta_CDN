FROM python:3.9-slim
COPY .aws/credentials /root/.aws/credentials
COPY .aws/config  /root/.aws/config
WORKDIR /app
COPY . /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
CMD ["python", "app.py"]
