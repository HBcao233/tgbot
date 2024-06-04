import asyncio
import httpx
from functools import cmp_to_key
import base64
import gzip
import struct

import util
import config
from util.log import logger
from .auth import getMixinKey, wbi, appsign, appkey
from .app import (
  FawkesReq,
  Metadata,
  Device,
  Network,
  Locale,
  PlayViewReq, 
  PlayViewReply,
)
from google.protobuf.json_format import MessageToDict


qn = 64

def _cmp(x, y):
  if x['id'] > qn:
    return 1
  if y['id'] > qn:
    return -1
  if x['id'] == y['id'] == qn:
    if x['codecid'] == 12:
      return -1
    if y['codecid'] == 12:
      return 1
    return 0
  if x['id'] < y['id']:
    return 1
  if x['id'] > y['id']:
    return -1
  return 0
  
  
async def getVideo(bvid, aid, cid):
  if config.bili_access_token == '':
    videos, audios = await _get(aid, cid)
  else:
    videos, audios = await _post(aid, cid)
  
  video_url = None
  audio_url = None
  if audios is None:
    video_url = videos
  else:
    # _videos = list(filter(lambda x: x['id']==qn, videos))
    videos = sorted(videos, key=cmp_to_key(_cmp))
    logger.info(f"qn: {videos[0]['id']}, codecid: {videos[0]['codecid']}")
    video_url = videos[0]['base_url']
    for i in audios:
      if i['id'] == 30216:
        audio_url = i['base_url']
        break
  
  #v_md5 = util.md5sum(video_url)
  #a_md5 = util.md5sum(audio_url)
  result = await asyncio.gather(
    util.getImg(
      video_url,
      headers=dict(config.bili_headers, **{'Referer': 'https://www.bilibili.com'}),
    ), 
    util.getImg(
      audio_url,
      headers=dict(config.bili_headers, **{'Referer': 'https://www.bilibili.com'}),
    ),
  ) 
  path = util.getCache(f'{bvid}.mp4')
  command = ['ffmpeg', '-i', result[0]]
  if result[1] != '':
    command.extend(['-i', result[1]])
  command.extend(['-c:v', 'copy', '-c:a', 'copy', '-y', path])
  logger.info(f'{command = }')
  proc = await asyncio.create_subprocess_exec(
    *command,
    stdout=asyncio.subprocess.PIPE, 
    stdin=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
  )
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.warning(stderr.decode('utf8'))
  
  return util.videoInfo(path)

async def _get(aid, cid):
  url = 'https://api.bilibili.com/x/player/wbi/playurl'
  mixin_key = await getMixinKey()
  params = {
    'fnver': 0,
    'fnval': 16,
    'qn': qn,
    'avid': aid,
    'cid': cid,
  }
  headers = {
    'Referer': 'https://www.bilibili.com',
  }
  r = await util.get(
    url,
    headers=dict(config.bili_headers, **headers),
    params=wbi(mixin_key, params),
  )
  logger.info(r.text)
  res = r.json()['data']
  if 'dash' in res:
    return res['dash']['video'], res['dash']['audio']
  return res['durl'][0]['url'], None
  
  
dalvikVer = "2.1.0"
osVer = "11"
brand = "M2012K11AC"
model = "Build/RKQ1.200826.002"
appVer = "7.32.0"
build = 7320200
cronet = "1.36.1"
buvid = "XX773E7376C5037B7772F0A6FA4439EDDC8DA"
channel = "xiaomi_cn_tv.danmaku.bili_zm20200902"
mobiApp = "android_tv_yst"
platform = "platform"


async def _post(aid, cid):
  url = 'https://grpc.biliapi.net/bilibili.pgc.gateway.player.v1.PlayURL/PlayView'
  headers = {
    'Host': 'grpc.biliapi.net',
    'Referer': 'www.bilibili.com',
    'content-type': 'application/grpc',
    'authorization': f'identify_v1 {config.bili_access_token}',
    'user-agent': f'Dalvik/{dalvikVer} (Linux; U; Android {osVer}; {brand} {model}) {appVer} os/android model/{brand} mobi_app/{mobiApp} build/{build} channel/{channel} innerVer/{build} osVer/{osVer} network/2 grpc-java-cronet/{cronet}',
    'te': 'trailers',
    'x-bili-fawkes-req-bin': GenerateFawkesReqBin(),
    'x-bili-metadata-bin': GenerateMetadataBin(),
    'x-bili-device-bin': GenerateDeviceBin(),
    'x-bili-network-bin': GenerateNetworkBin(),
    'x-bili-restriction-bin': '',
    'x-bili-locale-bin': GenerateLocaleBin(),
    'x-bili-exps-bin': '',
    'grpc-encoding': 'gzip',
    'grpc-accept-encoding': 'identity,gzip',
    'grpc-timeout': '17996161u',
  }
  logger.info(headers)
  data = PlayViewReq(
    epId=aid,
    cid=cid,
    qn=qn,
    fnval=16,
    spmid="pgc.pgc-video-detail.0.0",
    fromSpmid="default-value",
    preferCodecType=2,
    download=0,
    forceHost=2,
  )
  logger.info(MessageToDict(data))
  data = data.SerializeToString()
  data = gzip.compress(data)
  CLEAR_GZIP_HEADER = bytes([31, 139, 8, 0, 0, 0, 0, 0, 0, 0])
  data = CLEAR_GZIP_HEADER + data[10:]
  data = struct.pack("!bl", 1, len(data)) + data
  
  r = httpx.post(
    url,
    headers=headers,
    data=data,
  )
  logger.info(r.content)
  res = PlayViewReply()
  res.ParseFromString(r.content)
  return 

def GenerateFawkesReqBin():
  obj = FawkesReq(
    appkey="android64",
    env="prod",
    sessionId="dedf8669",
  )
  return serialize_base64(obj)
  
def GenerateMetadataBin():
  obj = Metadata(
    accessKey=appkey,
    mobiApp=mobiApp,
    build=build,
    channel=channel,
    buvid=buvid,
    platform=platform,
  )
  return serialize_base64(obj)

def GenerateDeviceBin():
  obj = Device(
    appId=1,
    build=build,
    buvid=buvid,
    mobiApp=mobiApp,
    platform=platform,
    channel=channel,
    brand=brand,
    model=model,
    osVer=osVer,
  )
  return serialize_base64(obj)
  
def GenerateNetworkBin():
  obj = Network(
    type=Network.TYPE.WIFI,
    tf=0,
    oid="46007"
  )
  return serialize_base64(obj)

def GenerateLocaleBin():
  obj = Locale(
    cLocale=Locale.LocaleIds(
      language="zh",
      region="CN",
    )
  )
  return serialize_base64(obj)
  
def serialize_base64(obj):
  return base64.b64encode(obj.SerializeToString()).decode("utf-8").rstrip("=")
  