# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PlayViewReply.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13PlayViewReply.proto\"\xca\x01\n\tVideoInfo\x12\x0f\n\x07quality\x18\x01 \x01(\r\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x12\n\ntimelength\x18\x03 \x01(\x04\x12\x14\n\x0cvideoCodecid\x18\x04 \x01(\r\x12\x1f\n\nstreamList\x18\x05 \x03(\x0b\x32\x0b.StreamItem\x12\x1c\n\tdashAudio\x18\x06 \x03(\x0b\x32\t.DashItem\x12\x19\n\x05\x64olby\x18\x07 \x01(\x0b\x32\n.DolbyItem\x12\x18\n\x04\x66lac\x18\t \x01(\x0b\x32\n.DolbyItem\"3\n\tDolbyItem\x12\x0c\n\x04type\x18\x01 \x01(\x05\x12\x18\n\x05\x61udio\x18\x02 \x01(\x0b\x32\t.DashItem\"\xe6\x04\n\x0fPlayAbilityConf\x12\x1d\n\x15\x62\x61\x63kgroundPlayDisable\x18\x01 \x01(\x08\x12\x13\n\x0b\x66lipDisable\x18\x02 \x01(\x08\x12\x13\n\x0b\x63\x61stDisable\x18\x03 \x01(\x08\x12\x17\n\x0f\x66\x65\x65\x64\x62\x61\x63kDisable\x18\x04 \x01(\x08\x12\x17\n\x0fsubtitleDisable\x18\x05 \x01(\x08\x12\x1b\n\x13playbackRateDisable\x18\x06 \x01(\x08\x12\x15\n\rtimeUpDisable\x18\x07 \x01(\x08\x12\x1b\n\x13playbackModeDisable\x18\x08 \x01(\x08\x12\x18\n\x10scaleModeDisable\x18\t \x01(\x08\x12\x13\n\x0blikeDisable\x18\n \x01(\x08\x12\x16\n\x0e\x64islikeDisable\x18\x0b \x01(\x08\x12\x13\n\x0b\x63oinDisable\x18\x0c \x01(\x08\x12\x13\n\x0b\x65lecDisable\x18\r \x01(\x08\x12\x14\n\x0cshareDisable\x18\x0e \x01(\x08\x12\x19\n\x11screenShotDisable\x18\x0f \x01(\x08\x12\x19\n\x11lockScreenDisable\x18\x10 \x01(\x08\x12\x18\n\x10recommendDisable\x18\x11 \x01(\x08\x12\x1c\n\x14playbackSpeedDisable\x18\x12 \x01(\x08\x12\x19\n\x11\x64\x65\x66initionDisable\x18\x13 \x01(\x08\x12\x19\n\x11selectionsDisable\x18\x14 \x01(\x08\x12\x13\n\x0bnextDisable\x18\x15 \x01(\x08\x12\x15\n\reditDmDisable\x18\x16 \x01(\x08\x12\x1a\n\x12smallWindowDisable\x18\x17 \x01(\x08\x12\x14\n\x0cshakeDisable\x18\x18 \x01(\x08\"9\n\x08\x43lipInfo\x12\r\n\x05start\x18\x02 \x01(\x05\x12\x0b\n\x03\x65nd\x18\x03 \x01(\x05\x12\x11\n\ttoastText\x18\x05 \x01(\t\"_\n\x0c\x42usinessInfo\x12\x11\n\tisPreview\x18\x01 \x01(\x08\x12\n\n\x02\x62p\x18\x02 \x01(\x08\x12\x13\n\x0bmarlinToken\x18\x03 \x01(\t\x12\x1b\n\x08\x63lipInfo\x18\x06 \x03(\x0b\x32\t.ClipInfo\"\x1e\n\x05\x45vent\x12\x15\n\x05shake\x18\x01 \x01(\x0b\x32\x06.Shake\"\x15\n\x05Shake\x12\x0c\n\x04\x66ile\x18\x01 \x01(\t\"y\n\x08\x44\x61shItem\x12\n\n\x02id\x18\x01 \x01(\r\x12\x0f\n\x07\x62\x61seUrl\x18\x02 \x01(\t\x12\x11\n\tbackupUrl\x18\x03 \x03(\t\x12\x11\n\tbandwidth\x18\x04 \x01(\r\x12\x0f\n\x07\x63odecid\x18\x05 \x01(\r\x12\x0b\n\x03md5\x18\x06 \x01(\t\x12\x0c\n\x04size\x18\x07 \x01(\x04\"q\n\nStreamItem\x12\x1f\n\nstreamInfo\x18\x01 \x01(\x0b\x32\x0b.StreamInfo\x12\x1d\n\tdashVideo\x18\x02 \x01(\x0b\x32\n.DashVideo\x12#\n\x0csegmentVideo\x18\x03 \x01(\x0b\x32\r.SegmentVideo\"\xca\x01\n\nStreamInfo\x12\x0f\n\x07quality\x18\x01 \x01(\r\x12\x0e\n\x06\x66ormat\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\x12\x0f\n\x07\x65rrCode\x18\x04 \x01(\r\x12\x1b\n\x05limit\x18\x05 \x01(\x0b\x32\x0c.StreamLimit\x12\x0f\n\x07needVip\x18\x06 \x01(\x08\x12\x11\n\tneedLogin\x18\x07 \x01(\x08\x12\x0e\n\x06intact\x18\x08 \x01(\x08\x12\x11\n\tnoRexcode\x18\t \x01(\x08\x12\x11\n\tattribute\x18\n \x01(\x04\"\x92\x01\n\tDashVideo\x12\x0f\n\x07\x62\x61seUrl\x18\x01 \x01(\t\x12\x11\n\tbackupUrl\x18\x02 \x03(\t\x12\x11\n\tbandwidth\x18\x03 \x01(\r\x12\x0f\n\x07\x63odecid\x18\x04 \x01(\r\x12\x0b\n\x03md5\x18\x05 \x01(\t\x12\x0c\n\x04size\x18\x06 \x01(\x04\x12\x0f\n\x07\x61udioId\x18\x07 \x01(\r\x12\x11\n\tnoRexcode\x18\x08 \x01(\x08\"-\n\x0cSegmentVideo\x12\x1d\n\x07segment\x18\x01 \x03(\x0b\x32\x0c.ResponseUrl\"6\n\x0bStreamLimit\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0b\n\x03uri\x18\x02 \x01(\t\x12\x0b\n\x03msg\x18\x03 \x01(\t\"g\n\x0bResponseUrl\x12\r\n\x05order\x18\x01 \x01(\r\x12\x0e\n\x06length\x18\x02 \x01(\x04\x12\x0c\n\x04size\x18\x03 \x01(\x04\x12\x0b\n\x03url\x18\x04 \x01(\t\x12\x11\n\tbackupUrl\x18\x05 \x03(\t\x12\x0b\n\x03md5\x18\x06 \x01(\t\"@\n\x0eRoleAudioProto\x12.\n\x11\x61udioMaterialList\x18\x04 \x03(\x0b\x32\x13.AudioMaterialProto\"s\n\x12\x41udioMaterialProto\x12\x0f\n\x07\x61udioId\x18\x01 \x01(\t\x12\r\n\x05title\x18\x02 \x01(\t\x12\x0f\n\x07\x65\x64ition\x18\x03 \x01(\t\x12\x12\n\npersonName\x18\x05 \x01(\t\x12\x18\n\x05\x61udio\x18\x07 \x03(\x0b\x32\t.DashItem\"g\n\x0fPlayDubbingInfo\x12,\n\x0f\x62\x61\x63kgroundAudio\x18\x01 \x01(\x0b\x32\x13.AudioMaterialProto\x12&\n\rroleAudioList\x18\x02 \x03(\x0b\x32\x0f.RoleAudioProto\"8\n\x0bPlayExtInfo\x12)\n\x0fplayDubbingInfo\x18\x01 \x01(\x0b\x32\x10.PlayDubbingInfo\"\xad\x01\n\rPlayViewReply\x12\x1d\n\tvideoInfo\x18\x01 \x01(\x0b\x32\n.VideoInfo\x12\"\n\x08playConf\x18\x02 \x01(\x0b\x32\x10.PlayAbilityConf\x12\x1f\n\x08\x62usiness\x18\x03 \x01(\x0b\x32\r.BusinessInfo\x12\x15\n\x05\x65vent\x18\x04 \x01(\x0b\x32\x06.Event\x12!\n\x0bplayExtInfo\x18\x07 \x01(\x0b\x32\x0c.PlayExtInfo')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'PlayViewReply_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_VIDEOINFO']._serialized_start=24
  _globals['_VIDEOINFO']._serialized_end=226
  _globals['_DOLBYITEM']._serialized_start=228
  _globals['_DOLBYITEM']._serialized_end=279
  _globals['_PLAYABILITYCONF']._serialized_start=282
  _globals['_PLAYABILITYCONF']._serialized_end=896
  _globals['_CLIPINFO']._serialized_start=898
  _globals['_CLIPINFO']._serialized_end=955
  _globals['_BUSINESSINFO']._serialized_start=957
  _globals['_BUSINESSINFO']._serialized_end=1052
  _globals['_EVENT']._serialized_start=1054
  _globals['_EVENT']._serialized_end=1084
  _globals['_SHAKE']._serialized_start=1086
  _globals['_SHAKE']._serialized_end=1107
  _globals['_DASHITEM']._serialized_start=1109
  _globals['_DASHITEM']._serialized_end=1230
  _globals['_STREAMITEM']._serialized_start=1232
  _globals['_STREAMITEM']._serialized_end=1345
  _globals['_STREAMINFO']._serialized_start=1348
  _globals['_STREAMINFO']._serialized_end=1550
  _globals['_DASHVIDEO']._serialized_start=1553
  _globals['_DASHVIDEO']._serialized_end=1699
  _globals['_SEGMENTVIDEO']._serialized_start=1701
  _globals['_SEGMENTVIDEO']._serialized_end=1746
  _globals['_STREAMLIMIT']._serialized_start=1748
  _globals['_STREAMLIMIT']._serialized_end=1802
  _globals['_RESPONSEURL']._serialized_start=1804
  _globals['_RESPONSEURL']._serialized_end=1907
  _globals['_ROLEAUDIOPROTO']._serialized_start=1909
  _globals['_ROLEAUDIOPROTO']._serialized_end=1973
  _globals['_AUDIOMATERIALPROTO']._serialized_start=1975
  _globals['_AUDIOMATERIALPROTO']._serialized_end=2090
  _globals['_PLAYDUBBINGINFO']._serialized_start=2092
  _globals['_PLAYDUBBINGINFO']._serialized_end=2195
  _globals['_PLAYEXTINFO']._serialized_start=2197
  _globals['_PLAYEXTINFO']._serialized_end=2253
  _globals['_PLAYVIEWREPLY']._serialized_start=2256
  _globals['_PLAYVIEWREPLY']._serialized_end=2429
# @@protoc_insertion_point(module_scope)