# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: Idm_service.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11Idm_service.proto\"!\n\x0eGetUserRequest\x12\x0f\n\x07user_id\x18\x01 \x01(\t\"\x8a\x01\n\x0fGetUserResponse\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\tlast_name\x18\x04 \x01(\t\x12\x12\n\nfirst_name\x18\x05 \x01(\t\x12\r\n\x05phone\x18\x06 \x01(\t\x12\r\n\x05\x65mail\x18\x07 \x01(\t\x12\x0f\n\x07\x63ountry\x18\x08 \x01(\t\x12\x0f\n\x07message\x18\t \x01(\t\"$\n\x11\x44\x65leteUserRequest\x12\x0f\n\x07user_id\x18\x01 \x01(\t\"H\n\x11UpdateUserRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x0f\n\x07id_user\x18\x03 \x01(\t\"3\n\x12\x44\x65leteUserResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\"D\n\x12UpdateUserResponse\x12\x0f\n\x07id_user\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0c\n\x04\x63ode\x18\x03 \x01(\x05\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"D\n\rLoginResponse\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0c\n\x04\x63ode\x18\x03 \x01(\x05\"\x1d\n\x0cTokenRequest\x12\r\n\x05token\x18\x01 \x01(\t\"2\n\rTokenResponse\x12\x10\n\x08is_valid\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x89\x01\n\rSignUpRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x11\n\tlast_name\x18\x04 \x01(\t\x12\x12\n\nfirst_name\x18\x05 \x01(\t\x12\r\n\x05phone\x18\x06 \x01(\t\x12\r\n\x05\x65mail\x18\x07 \x01(\t\x12\x0f\n\x07\x63ountry\x18\x08 \x01(\t\"V\n\x0eSignUpResponse\x12\x14\n\x0c\x61\x63\x63\x65ss_token\x18\x01 \x01(\t\x12\x0f\n\x07id_user\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\x12\x0c\n\x04\x63ode\x18\x04 \x01(\x05\x32\xad\x02\n\nIDMService\x12&\n\x05Login\x12\r.LoginRequest\x1a\x0e.LoginResponse\x12,\n\x0bVerifyToken\x12\r.TokenRequest\x1a\x0e.TokenResponse\x12)\n\x06SignUp\x12\x0e.SignUpRequest\x1a\x0f.SignUpResponse\x12\x35\n\nDeleteUser\x12\x12.DeleteUserRequest\x1a\x13.DeleteUserResponse\x12\x35\n\nUpdateUser\x12\x12.UpdateUserRequest\x1a\x13.UpdateUserResponse\x12\x30\n\x0bGetUserData\x12\x0f.GetUserRequest\x1a\x10.GetUserResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'Idm_service_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_GETUSERREQUEST']._serialized_start=21
  _globals['_GETUSERREQUEST']._serialized_end=54
  _globals['_GETUSERRESPONSE']._serialized_start=57
  _globals['_GETUSERRESPONSE']._serialized_end=195
  _globals['_DELETEUSERREQUEST']._serialized_start=197
  _globals['_DELETEUSERREQUEST']._serialized_end=233
  _globals['_UPDATEUSERREQUEST']._serialized_start=235
  _globals['_UPDATEUSERREQUEST']._serialized_end=307
  _globals['_DELETEUSERRESPONSE']._serialized_start=309
  _globals['_DELETEUSERRESPONSE']._serialized_end=360
  _globals['_UPDATEUSERRESPONSE']._serialized_start=362
  _globals['_UPDATEUSERRESPONSE']._serialized_end=430
  _globals['_LOGINREQUEST']._serialized_start=432
  _globals['_LOGINREQUEST']._serialized_end=482
  _globals['_LOGINRESPONSE']._serialized_start=484
  _globals['_LOGINRESPONSE']._serialized_end=552
  _globals['_TOKENREQUEST']._serialized_start=554
  _globals['_TOKENREQUEST']._serialized_end=583
  _globals['_TOKENRESPONSE']._serialized_start=585
  _globals['_TOKENRESPONSE']._serialized_end=635
  _globals['_SIGNUPREQUEST']._serialized_start=638
  _globals['_SIGNUPREQUEST']._serialized_end=775
  _globals['_SIGNUPRESPONSE']._serialized_start=777
  _globals['_SIGNUPRESPONSE']._serialized_end=863
  _globals['_IDMSERVICE']._serialized_start=866
  _globals['_IDMSERVICE']._serialized_end=1167
# @@protoc_insertion_point(module_scope)
