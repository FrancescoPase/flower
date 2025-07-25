# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: flwr/proto/clientappio.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from flwr.proto import fab_pb2 as flwr_dot_proto_dot_fab__pb2
from flwr.proto import run_pb2 as flwr_dot_proto_dot_run__pb2
from flwr.proto import message_pb2 as flwr_dot_proto_dot_message__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1c\x66lwr/proto/clientappio.proto\x12\nflwr.proto\x1a\x14\x66lwr/proto/fab.proto\x1a\x14\x66lwr/proto/run.proto\x1a\x18\x66lwr/proto/message.proto\"%\n#GetRunIdsWithPendingMessagesRequest\"7\n$GetRunIdsWithPendingMessagesResponse\x12\x0f\n\x07run_ids\x18\x01 \x03(\x04\"%\n\x13RequestTokenRequest\x12\x0e\n\x06run_id\x18\x01 \x01(\x04\"%\n\x14RequestTokenResponse\x12\r\n\x05token\x18\x01 \x01(\t\"W\n\x15\x43lientAppOutputStatus\x12-\n\x04\x63ode\x18\x01 \x01(\x0e\x32\x1f.flwr.proto.ClientAppOutputCode\x12\x0f\n\x07message\x18\x02 \x01(\t\"+\n\x1aPullClientAppInputsRequest\x12\r\n\x05token\x18\x01 \x01(\t\"\x7f\n\x1bPullClientAppInputsResponse\x12$\n\x07\x63ontext\x18\x01 \x01(\x0b\x32\x13.flwr.proto.Context\x12\x1c\n\x03run\x18\x02 \x01(\x0b\x32\x0f.flwr.proto.Run\x12\x1c\n\x03\x66\x61\x62\x18\x03 \x01(\x0b\x32\x0f.flwr.proto.Fab\"R\n\x1bPushClientAppOutputsRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12$\n\x07\x63ontext\x18\x02 \x01(\x0b\x32\x13.flwr.proto.Context\"Q\n\x1cPushClientAppOutputsResponse\x12\x31\n\x06status\x18\x01 \x01(\x0b\x32!.flwr.proto.ClientAppOutputStatus\"#\n\x12PullMessageRequest\x12\r\n\x05token\x18\x01 \x01(\t\";\n\x13PullMessageResponse\x12$\n\x07message\x18\x01 \x01(\x0b\x32\x13.flwr.proto.Message\"I\n\x12PushMessageRequest\x12\r\n\x05token\x18\x01 \x01(\t\x12$\n\x07message\x18\x02 \x01(\x0b\x32\x13.flwr.proto.Message\"\x15\n\x13PushMessageResponse*L\n\x13\x43lientAppOutputCode\x12\x0b\n\x07SUCCESS\x10\x00\x12\x15\n\x11\x44\x45\x41\x44LINE_EXCEEDED\x10\x01\x12\x11\n\rUNKNOWN_ERROR\x10\x02\x32\xe3\x04\n\x0b\x43lientAppIo\x12\x83\x01\n\x1cGetRunIdsWithPendingMessages\x12/.flwr.proto.GetRunIdsWithPendingMessagesRequest\x1a\x30.flwr.proto.GetRunIdsWithPendingMessagesResponse\"\x00\x12S\n\x0cRequestToken\x12\x1f.flwr.proto.RequestTokenRequest\x1a .flwr.proto.RequestTokenResponse\"\x00\x12h\n\x13PullClientAppInputs\x12&.flwr.proto.PullClientAppInputsRequest\x1a\'.flwr.proto.PullClientAppInputsResponse\"\x00\x12k\n\x14PushClientAppOutputs\x12\'.flwr.proto.PushClientAppOutputsRequest\x1a(.flwr.proto.PushClientAppOutputsResponse\"\x00\x12P\n\x0bPushMessage\x12\x1e.flwr.proto.PushMessageRequest\x1a\x1f.flwr.proto.PushMessageResponse\"\x00\x12P\n\x0bPullMessage\x12\x1e.flwr.proto.PullMessageRequest\x1a\x1f.flwr.proto.PullMessageResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'flwr.proto.clientappio_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_CLIENTAPPOUTPUTCODE']._serialized_start=914
  _globals['_CLIENTAPPOUTPUTCODE']._serialized_end=990
  _globals['_GETRUNIDSWITHPENDINGMESSAGESREQUEST']._serialized_start=114
  _globals['_GETRUNIDSWITHPENDINGMESSAGESREQUEST']._serialized_end=151
  _globals['_GETRUNIDSWITHPENDINGMESSAGESRESPONSE']._serialized_start=153
  _globals['_GETRUNIDSWITHPENDINGMESSAGESRESPONSE']._serialized_end=208
  _globals['_REQUESTTOKENREQUEST']._serialized_start=210
  _globals['_REQUESTTOKENREQUEST']._serialized_end=247
  _globals['_REQUESTTOKENRESPONSE']._serialized_start=249
  _globals['_REQUESTTOKENRESPONSE']._serialized_end=286
  _globals['_CLIENTAPPOUTPUTSTATUS']._serialized_start=288
  _globals['_CLIENTAPPOUTPUTSTATUS']._serialized_end=375
  _globals['_PULLCLIENTAPPINPUTSREQUEST']._serialized_start=377
  _globals['_PULLCLIENTAPPINPUTSREQUEST']._serialized_end=420
  _globals['_PULLCLIENTAPPINPUTSRESPONSE']._serialized_start=422
  _globals['_PULLCLIENTAPPINPUTSRESPONSE']._serialized_end=549
  _globals['_PUSHCLIENTAPPOUTPUTSREQUEST']._serialized_start=551
  _globals['_PUSHCLIENTAPPOUTPUTSREQUEST']._serialized_end=633
  _globals['_PUSHCLIENTAPPOUTPUTSRESPONSE']._serialized_start=635
  _globals['_PUSHCLIENTAPPOUTPUTSRESPONSE']._serialized_end=716
  _globals['_PULLMESSAGEREQUEST']._serialized_start=718
  _globals['_PULLMESSAGEREQUEST']._serialized_end=753
  _globals['_PULLMESSAGERESPONSE']._serialized_start=755
  _globals['_PULLMESSAGERESPONSE']._serialized_end=814
  _globals['_PUSHMESSAGEREQUEST']._serialized_start=816
  _globals['_PUSHMESSAGEREQUEST']._serialized_end=889
  _globals['_PUSHMESSAGERESPONSE']._serialized_start=891
  _globals['_PUSHMESSAGERESPONSE']._serialized_end=912
  _globals['_CLIENTAPPIO']._serialized_start=993
  _globals['_CLIENTAPPIO']._serialized_end=1604
# @@protoc_insertion_point(module_scope)
