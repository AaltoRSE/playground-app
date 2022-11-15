# ===================================================================================
# Copyright (C) 2019 Fraunhofer Gesellschaft. All rights reserved.
# ===================================================================================
# This Graphene software file is distributed by Fraunhofer Gesellschaft
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END==========================================================
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: orchestrator.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='orchestrator.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x12orchestrator.proto\"\x19\n\x08RunLabel\x12\r\n\x05label\x18\x01 \x01(\t\"\xde\x01\n\x1aOrchestrationConfiguration\x12\x11\n\tblueprint\x18\x01 \x01(\t\x12\x12\n\ndockerinfo\x18\x02 \x01(\t\x12?\n\nprotofiles\x18\x03 \x03(\x0b\x32+.OrchestrationConfiguration.ProtofilesEntry\x12\x11\n\tqueuesize\x18\x04 \x01(\x05\x12\x12\n\niterations\x18\x05 \x01(\x05\x1a\x31\n\x0fProtofilesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"]\n\x13OrchestrationStatus\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0c\n\x04\x63ode\x18\x02 \x01(\x05\x12\x0f\n\x07message\x18\x03 \x01(\t\x12\x16\n\x0e\x61\x63tive_threads\x18\x04 \x01(\x05\"T\n%OrchestrationObservationConfiguration\x12\x12\n\nname_regex\x18\x01 \x01(\t\x12\x17\n\x0f\x63omponent_regex\x18\x02 \x01(\t\"\xa2\x01\n\x12OrchestrationEvent\x12\x0b\n\x03run\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x11\n\tcomponent\x18\x03 \x01(\t\x12/\n\x06\x64\x65tail\x18\x04 \x03(\x0b\x32\x1f.OrchestrationEvent.DetailEntry\x1a-\n\x0b\x44\x65tailEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x32\xf0\x01\n\x0cOrchestrator\x12?\n\ninitialize\x12\x1b.OrchestrationConfiguration\x1a\x14.OrchestrationStatus\x12H\n\x07observe\x12&.OrchestrationObservationConfiguration\x1a\x13.OrchestrationEvent0\x01\x12&\n\x03run\x12\t.RunLabel\x1a\x14.OrchestrationStatus\x12-\n\nget_status\x12\t.RunLabel\x1a\x14.OrchestrationStatusb\x06proto3'
)




_RUNLABEL = _descriptor.Descriptor(
  name='RunLabel',
  full_name='RunLabel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='label', full_name='RunLabel.label', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=47,
)


_ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY = _descriptor.Descriptor(
  name='ProtofilesEntry',
  full_name='OrchestrationConfiguration.ProtofilesEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='OrchestrationConfiguration.ProtofilesEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='OrchestrationConfiguration.ProtofilesEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=223,
  serialized_end=272,
)

_ORCHESTRATIONCONFIGURATION = _descriptor.Descriptor(
  name='OrchestrationConfiguration',
  full_name='OrchestrationConfiguration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='blueprint', full_name='OrchestrationConfiguration.blueprint', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dockerinfo', full_name='OrchestrationConfiguration.dockerinfo', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='protofiles', full_name='OrchestrationConfiguration.protofiles', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='queuesize', full_name='OrchestrationConfiguration.queuesize', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='iterations', full_name='OrchestrationConfiguration.iterations', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=50,
  serialized_end=272,
)


_ORCHESTRATIONSTATUS = _descriptor.Descriptor(
  name='OrchestrationStatus',
  full_name='OrchestrationStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='success', full_name='OrchestrationStatus.success', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='code', full_name='OrchestrationStatus.code', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message', full_name='OrchestrationStatus.message', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='active_threads', full_name='OrchestrationStatus.active_threads', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=274,
  serialized_end=367,
)


_ORCHESTRATIONOBSERVATIONCONFIGURATION = _descriptor.Descriptor(
  name='OrchestrationObservationConfiguration',
  full_name='OrchestrationObservationConfiguration',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name_regex', full_name='OrchestrationObservationConfiguration.name_regex', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='component_regex', full_name='OrchestrationObservationConfiguration.component_regex', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=369,
  serialized_end=453,
)


_ORCHESTRATIONEVENT_DETAILENTRY = _descriptor.Descriptor(
  name='DetailEntry',
  full_name='OrchestrationEvent.DetailEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='OrchestrationEvent.DetailEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='OrchestrationEvent.DetailEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=573,
  serialized_end=618,
)

_ORCHESTRATIONEVENT = _descriptor.Descriptor(
  name='OrchestrationEvent',
  full_name='OrchestrationEvent',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='run', full_name='OrchestrationEvent.run', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='name', full_name='OrchestrationEvent.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='component', full_name='OrchestrationEvent.component', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='detail', full_name='OrchestrationEvent.detail', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_ORCHESTRATIONEVENT_DETAILENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=456,
  serialized_end=618,
)

_ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY.containing_type = _ORCHESTRATIONCONFIGURATION
_ORCHESTRATIONCONFIGURATION.fields_by_name['protofiles'].message_type = _ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY
_ORCHESTRATIONEVENT_DETAILENTRY.containing_type = _ORCHESTRATIONEVENT
_ORCHESTRATIONEVENT.fields_by_name['detail'].message_type = _ORCHESTRATIONEVENT_DETAILENTRY
DESCRIPTOR.message_types_by_name['RunLabel'] = _RUNLABEL
DESCRIPTOR.message_types_by_name['OrchestrationConfiguration'] = _ORCHESTRATIONCONFIGURATION
DESCRIPTOR.message_types_by_name['OrchestrationStatus'] = _ORCHESTRATIONSTATUS
DESCRIPTOR.message_types_by_name['OrchestrationObservationConfiguration'] = _ORCHESTRATIONOBSERVATIONCONFIGURATION
DESCRIPTOR.message_types_by_name['OrchestrationEvent'] = _ORCHESTRATIONEVENT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

RunLabel = _reflection.GeneratedProtocolMessageType('RunLabel', (_message.Message,), {
  'DESCRIPTOR' : _RUNLABEL,
  '__module__' : 'orchestrator_pb2'
  # @@protoc_insertion_point(class_scope:RunLabel)
  })
_sym_db.RegisterMessage(RunLabel)

OrchestrationConfiguration = _reflection.GeneratedProtocolMessageType('OrchestrationConfiguration', (_message.Message,), {

  'ProtofilesEntry' : _reflection.GeneratedProtocolMessageType('ProtofilesEntry', (_message.Message,), {
    'DESCRIPTOR' : _ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY,
    '__module__' : 'orchestrator_pb2'
    # @@protoc_insertion_point(class_scope:OrchestrationConfiguration.ProtofilesEntry)
    })
  ,
  'DESCRIPTOR' : _ORCHESTRATIONCONFIGURATION,
  '__module__' : 'orchestrator_pb2'
  # @@protoc_insertion_point(class_scope:OrchestrationConfiguration)
  })
_sym_db.RegisterMessage(OrchestrationConfiguration)
_sym_db.RegisterMessage(OrchestrationConfiguration.ProtofilesEntry)

OrchestrationStatus = _reflection.GeneratedProtocolMessageType('OrchestrationStatus', (_message.Message,), {
  'DESCRIPTOR' : _ORCHESTRATIONSTATUS,
  '__module__' : 'orchestrator_pb2'
  # @@protoc_insertion_point(class_scope:OrchestrationStatus)
  })
_sym_db.RegisterMessage(OrchestrationStatus)

OrchestrationObservationConfiguration = _reflection.GeneratedProtocolMessageType('OrchestrationObservationConfiguration', (_message.Message,), {
  'DESCRIPTOR' : _ORCHESTRATIONOBSERVATIONCONFIGURATION,
  '__module__' : 'orchestrator_pb2'
  # @@protoc_insertion_point(class_scope:OrchestrationObservationConfiguration)
  })
_sym_db.RegisterMessage(OrchestrationObservationConfiguration)

OrchestrationEvent = _reflection.GeneratedProtocolMessageType('OrchestrationEvent', (_message.Message,), {

  'DetailEntry' : _reflection.GeneratedProtocolMessageType('DetailEntry', (_message.Message,), {
    'DESCRIPTOR' : _ORCHESTRATIONEVENT_DETAILENTRY,
    '__module__' : 'orchestrator_pb2'
    # @@protoc_insertion_point(class_scope:OrchestrationEvent.DetailEntry)
    })
  ,
  'DESCRIPTOR' : _ORCHESTRATIONEVENT,
  '__module__' : 'orchestrator_pb2'
  # @@protoc_insertion_point(class_scope:OrchestrationEvent)
  })
_sym_db.RegisterMessage(OrchestrationEvent)
_sym_db.RegisterMessage(OrchestrationEvent.DetailEntry)


_ORCHESTRATIONCONFIGURATION_PROTOFILESENTRY._options = None
_ORCHESTRATIONEVENT_DETAILENTRY._options = None

_ORCHESTRATOR = _descriptor.ServiceDescriptor(
  name='Orchestrator',
  full_name='Orchestrator',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=621,
  serialized_end=861,
  methods=[
  _descriptor.MethodDescriptor(
    name='initialize',
    full_name='Orchestrator.initialize',
    index=0,
    containing_service=None,
    input_type=_ORCHESTRATIONCONFIGURATION,
    output_type=_ORCHESTRATIONSTATUS,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='observe',
    full_name='Orchestrator.observe',
    index=1,
    containing_service=None,
    input_type=_ORCHESTRATIONOBSERVATIONCONFIGURATION,
    output_type=_ORCHESTRATIONEVENT,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='run',
    full_name='Orchestrator.run',
    index=2,
    containing_service=None,
    input_type=_RUNLABEL,
    output_type=_ORCHESTRATIONSTATUS,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='get_status',
    full_name='Orchestrator.get_status',
    index=3,
    containing_service=None,
    input_type=_RUNLABEL,
    output_type=_ORCHESTRATIONSTATUS,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_ORCHESTRATOR)

DESCRIPTOR.services_by_name['Orchestrator'] = _ORCHESTRATOR

# @@protoc_insertion_point(module_scope)