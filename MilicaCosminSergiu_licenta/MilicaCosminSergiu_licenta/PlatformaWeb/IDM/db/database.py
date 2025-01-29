from peewee import MySQLDatabase

db = MySQLDatabase(
    host='mariadb',
    user='cosmin',
    password='cosmin',
    database='user_db',
    port=3306
)