FROM python:3.9

WORKDIR /app
RUN pip install grpcio grpcio_tools bcrypt pyjwt peewee requests~=2.31.0
RUN pip install pymysql
COPY . .

CMD ["python", "UserService.py"]