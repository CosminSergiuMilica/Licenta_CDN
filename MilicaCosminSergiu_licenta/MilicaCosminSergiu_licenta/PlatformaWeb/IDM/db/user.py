from peewee import *
from .database import db
class User(Model):
    id = CharField(max_length=50, primary_key=True)
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=255)
    first_name = CharField(max_length=50)
    last_name = CharField(max_length=50)
    email = CharField(max_length=70, unique=True)
    type_user = CharField(max_length=5, choices=('admin', 'user'))
    phone = CharField(max_length=10, unique=True, constraints=[Check('phone REGEXP "^07[0-9]{8}$"')])
    country = CharField(max_length=50, null=True)

    class Meta:
        database = db
        table_name = 'user'