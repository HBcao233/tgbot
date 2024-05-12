import re
import asyncio
import traceback
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InlineQueryResultsButton,
    InputTextMessageContent,
    InlineQueryResultPhoto,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
)
from telegram.ext import ContextTypes
from uuid import uuid4
import dateutil.parser
import datetime
import os.path
from functools import reduce
import time
import urllib.parse
import hashlib
import httpx
import ujson as json

import config
import util
from util.log import logger
from plugin import handler, inline_handler, button_handler


_pattern = r"(?:^|bilibili\.com/video/)(av\d{1,11}|BV[0-9a-zA-Z]{8,12})|(?:b23\.tv/((?![0-9]{7,7})[0-9a-zA-Z]{7,7}))"
@handler('bili', 
  private_pattern=_pattern,
  info="av号或bv号获取视频"
)
async def _(update, context, text):
  bot = context.bot
  message = update.message
  logger.info(message)
  if text == "":
    return await bot.send_message(
      text="用法: /bill <aid/bvid>", 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  m = await bot.send_message(
    text="请等待...", 
    chat_id=message.chat.id, 
    reply_to_message_id=message.message_id,
  )
  
  match = re.search(_pattern, text)
  if match.group(2):
    r = httpx.get('https://b23.tv/'+ match.group(2), headers=config.bili_headers, follow_redirects=True)
    text = str(r.url).split('?')[0]
    match = re.search(_pattern, text)
    await bot.delete_message(chat_id=message.chat.id, message_id=m.message_id)
    await bot.send_message(
      text=text, 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
    m = await bot.send_message(
      text="请等待...", 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
    
  g = match.group(1)
  aid = ''
  bvid = ''
  if 'av' in g:
    aid = g.replace('av', '')
  else:
    bvid = g.replace('BV', '')
  r = await util.get(
    'https://api.bilibili.com/x/web-interface/view', 
    headers=config.bili_headers,
    params={
      'aid': aid,
      'bvid': bvid
    }
  )
  # logger.info(r.text)
  res = r.json()
  if res['code'] in [-404, 62002, 62004]:
    return await bot.send_message(
      text='视频不存在', 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  elif res['code'] != 0:
    return await bot.send_message(
      text='请求失败', 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  
  res = res['data']
  aid = res['aid']
  bvid = res['bvid']
  msg = (
    f"<a href=\"https://www.bilibili.com/video/{res['bvid']}\">{res['title']}</a> - "
    f"<a href=\"https://space.bilibili.com/{res['owner']['mid']}\">{res['owner']['name']}</a>"
  )
  
  try:
    data = util.getData('videos')
    logger.info(data)
    logger.info(f'bvid: {bvid} video: '+str(data.get(bvid, None)))
    if not (video := data.get(bvid, None)):
      mixin_key = await getMixinKey()
      url = 'https://api.bilibili.com/x/player/wbi/playurl'
      r1 = await util.get(
        url,
        headers=dict(config.bili_headers, **{'Referer': 'https://www.bilibili.com'}),
        params=wbi(mixin_key, {
          'fnver': 0,
          'fnval': 16,
          'qn': 64,
          'avid': aid,
          'cid': res['cid'],
        })
      )
      # logger.info(r1.text)
      res1 = r1.json()['data']
      # logger.info(json.dumps(res1['dash']['video']))
      # logger.info(json.dumps(res1['dash']['audio']))
      
      video_url = None
      audio_url = None
      videos = res1['dash']['video']
      audios = res1['dash']['audio']
      for i in videos:
        if i['id'] == 64:
          video_url = i['base_url']
          break
      for i in audios:
        if i['id'] == 30216:
          audio_url = i['base_url']
          break
      #v_md5 = util.md5sum(video_url)
      #a_md5 = util.md5sum(audio_url)
      result = await asyncio.gather(util.getImg(
        video_url,
        headers=dict(config.bili_headers, **{'Referer': 'https://www.bilibili.com'}),
      ), util.getImg(
        audio_url,
        headers=dict(config.bili_headers, **{'Referer': 'https://www.bilibili.com'}),
      )) 
      logger.info(result[0])
      proc = await asyncio.create_subprocess_exec(
        'ffmpeg', '-i', result[0], '-i', result[1], '-c:v', 'copy', '-c:a', 'copy', '-y', f'{config.botRoot}/data/cache/{bvid}.mp4',
        stdout=asyncio.subprocess.PIPE, 
        stdin=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
      )
      await proc.wait()
      video = open(config.botRoot + f'/data/cache/{bvid}.mp4', 'rb')
    
    m1 = await bot.send_video(
      video=video,
      caption=msg, 
      chat_id=message.chat.id,
      reply_to_message_id=message.message_id,
      parse_mode="HTML",
      read_timeout=60,
      write_timeout=60,
      connect_timeout=60,
      pool_timeout=60,
    )
    if not data.get(bvid, None):
      data[bvid] = m1.video.file_id
      util.setData('videos', data)
  except Exception:
    logger.error(traceback.print_exc())
    await bot.send_message(
      text='媒体发送失败', 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  await bot.delete_message(chat_id=message.chat.id, message_id=m.message_id)
    
 
async def getMixinKey():
  mixinKeyEncTab = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
  ]
  
  r = await util.get('https://api.bilibili.com/x/web-interface/nav', headers=config.bili_headers)
  res = r.json()['data']['wbi_img']
  img_key = res['img_url'].rsplit('/', 1)[1].split('.')[0]
  sub_key = res['sub_url'].rsplit('/', 1)[1].split('.')[0]
  orig = img_key + sub_key
  return reduce(lambda s, i: s + orig[i], mixinKeyEncTab, '')[:32]
 
    
def wbi(mixin_key, params=None):
  if params is None: params = dict()
  params['wts'] = round(time.time())
  params = dict(sorted(params.items()))                       # 按照 key 重排参数
  # 过滤 value 中的 "!'()*" 字符
  params = {
      k : ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
      for k, v in params.items()
  }
  query = urllib.parse.urlencode(params) # 序列化参数
  params['w_rid'] = hashlib.md5((query + mixin_key).encode()).hexdigest()
  return params