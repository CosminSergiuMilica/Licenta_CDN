import datetime
import logging
import re
from peewee import IntegrityError
import grpc
from grpc import *
from concurrent import futures
import time
import uuid
import bcrypt
import jwt
import re
import Idm_service_pb2
import Idm_service_pb2_grpc
from db.user import User
from db.database import db
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)
def connect_database():
    if db.is_closed():
        try:
            db.connect()
        except ConnectionError as e:
            print(e)

def close_database():
    if not db.is_closed():
        db.close()

def validate_email(email):
    pattern = r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+).[a-zA-Z]+$"
    if re.match(pattern, email):
        return True
    else:
        return False

SECRET_KEY = "GoSdJgsDEe343"
class UserService(Idm_service_pb2_grpc.IDMServiceServicer):

    def Login(self, request, context):
        username = request.username
        password = request.password
        user = User.get_or_none(User.username == username)
        if user is not None:
            if bcrypt.checkpw(password.encode(), user.password.encode()):
                payload = {
                    'iss': "http://web_platform-users-service-1:50051/Login",
                    'username': username,
                    'role': user.type_user,
                    'sub': str(user.id),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
                    'jti': str(uuid.uuid4())
                }
                jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
                return Idm_service_pb2.LoginResponse(
                    access_token=str(jwt_token),
                    message="Autentificare cu succes",
                    code=200
                )
            else:
                print("Parola incorecta")
                return Idm_service_pb2.LoginResponse(access_token=None,
                                                    message="Autentificare eșuata:  parola incorecte",
                                                    code=401)
        else:
            print("User incorect")
            return  Idm_service_pb2.LoginResponse(access_token=None,
                                                message="Autentificare eșuata: Utilizator  incorecte",
                                                code=401)


    def VerifyToken(self, request, context):
        jwt_token = request.token
        try:
            decoded_token = jwt.decode(jwt_token, SECRET_KEY, algorithms=['HS256'])

            return Idm_service_pb2.TokenResponse(
                message="Tokenul JWT este valid și autentic",
                is_valid='valid'
            )
        except jwt.ExpiredSignatureError:
            return Idm_service_pb2.TokenResponse(
                message="Tokenul JWT a expirat",
                is_valid='invalid'
            )
        except jwt.InvalidTokenError:
            return Idm_service_pb2.TokenResponse(
                message="Tokenul JWT este invalid sau corupt",
                is_valid='invalid'
            )

    def SignUp(self, request, context):
        username = request.username
        password = request.password
        last_name = request.last_name
        first_name = request.first_name
        phone = request.phone
        email = request.email
        country = request.country
        type_user = 'user'
        user_secret = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(password.encode(), user_secret)
        try:
            user_id = uuid.uuid4()
            payload = {
                'iss': "http://web_platform-users-service-1:50051/SignUp",
                'username': username,
                'role': type_user,
                'sub': str(user_id),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
                'jti': str(uuid.uuid4())
            }
            jwt_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            print(jwt_token)
            if jwt_token:
                with db.atomic() as transaction:
                    new_user = User.create(
                        id=str(user_id),
                        username=username,
                        password=hash_password,
                        type_user=type_user,
                        last_name=last_name,
                        first_name=first_name,
                        phone=phone,
                        email=email,
                        country=country
                    )
                transaction.commit()
            return Idm_service_pb2.SignUpResponse(
                access_token=str(jwt_token),
                id_user=str(user_id),
                message='Utilizator inregistrat cu succes',
                code=201
            )
        except IntegrityError as e:
            db.rollback()
            return Idm_service_pb2.SignUpResponse(message=f"Eroare la inregistrare", code=409)

    def DeleteUser(self, request, context):
        id_user = request.user_id
        try:
            with db.atomic():
                user = User.get_or_none(User.id == id_user)
                if user is None:
                    return Idm_service_pb2.DeleteUserResponse(message=f"Userul {id_user} nu exista", code=404)
                user.delete_instance()
                return Idm_service_pb2.DeleteUserResponse(message=f"User sters cu succes", code=204)
        except IntegrityError as e:
            return Idm_service_pb2.SignUpResponse(
                message=str(e),
                code=409
            )
        except Exception as e:
            return Idm_service_pb2.DeleteUserResponse(message=f"Eroare la înregistrare: {str(e)}", code=500)

    def UpdateUser(self, request, context):
        username = request.username
        password = request.password
        id_user = request.id_user

        try:
            user = User.get(User.id == id_user)
            user.username = username
            user.password = password
            user.save()
            return Idm_service_pb2.UpdateUserResponse(id_user=id_user, message="User actualizat cu succes", code=200)
        except User.DoesNotExist:
            return Idm_service_pb2.UpdateUserResponse(message="Userul nu a fost gasit", code=404)

    def GetUserData(self, request, context):
        id_user = request.user_id
        try:
            with db.atomic():
                user = User.get_or_none(User.id == id_user)
                if user is not None:
                    return Idm_service_pb2.GetUserResponse(
                        username=user.username,
                        last_name=user.last_name,
                        first_name=user.first_name,
                        phone=user.phone,
                        email=user.email,
                        country=user.country,
                        message=None
                    )
                else:
                    return Idm_service_pb2.GetUserResponse(
                        message=f"User with ID {id_user} not found"
                    )
        except IntegrityError as e:
            return Idm_service_pb2.GetUserResponse(
                message=str(e)
            )
        except Exception as e:
            return Idm_service_pb2.GetUserResponse(
                message="An error occurred"
            )

    def GetUserMail(self, request, context):
        id_user = request.user_id
        try:
            with db.atomic():
                email = User.select(User.email).where(User.id == id_user).scalar()
                if email is not None:
                    return Idm_service_pb2.GetMailResponse(
                        email=email,
                        code=200

                    )
                else:
                    return Idm_service_pb2.GetMailResponse(
                        email="",
                        code=404
                    )
        except Exception as e:
            return Idm_service_pb2.GetMailResponse(
                email="",
                code=500
            )


server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
Idm_service_pb2_grpc.add_IDMServiceServicer_to_server(UserService(), server)
server.add_insecure_port('[::]:50051')

print('Conectarea la baza de date...')
connect_database()

print('Pornirea serverului gRPC...')
server.start()

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    print('oprim server...')
finally:
    print('Închiderea conexiunii la baza de date...')
    close_database()
    server.stop(0)