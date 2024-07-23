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
import os.path
import httpx
import ujson as json

import util
from util.log import logger
from plugin import handler, inline_handler, button_handler
from .data_source import headers, getVideo


_pattern = r"(?:^|bilibili\.com/video/)(av\d{1,11}|BV[0-9a-zA-Z]{8,12})|(?:b23\.tv\\?/((?![0-9]{7,7})[0-9a-zA-Z]{7,7}))"
@handler('bili', 
  private_pattern=_pattern,
  info="av号或bv号获取视频"
)
async def _(update, context, text):
  bot = context.bot
  message = update.message
  # logger.info(message)
  if text == "":
    return await bot.send_message(
      text="用法: /bill <aid/bvid>", 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  
  arr = text.split(' ')
  nocache = False
  mark = False
  if 'nocache' in arr:
    nocache = True
  if 'mark' in arr:
    mark = True
  
  flag = 0
  match = re.search(_pattern, text)
  if match.group(2):
    r = httpx.get(
      'https://b23.tv/'+ match.group(2),
      follow_redirects=True,
      headers=headers,
    )
    text = str(r.url)
    match = re.search(_pattern, text.split('?')[0])
    flag = 1
    
  p = 1
  g = match.group(1)
  aid = ''
  bvid = ''
  if 'av' in g:
    aid = g.replace('av', '')
  else:
    bvid = g
  
  if (match1 := re.search(r'(?:\?|&)p=(\d+)', text)):
    if (_p := int(match1.group(1))) > 1:
      p = _p
      
  if flag:
    await bot.send_message(
      text=f'https://www.bilibili.com/video/{bvid}' + ('?p=' + str(p) if p>1 else ''), 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
    
  mid = await bot.send_message(
    text="请等待...", 
    chat_id=message.chat.id, 
    reply_to_message_id=message.message_id,
  )
    
  r = await util.get(
    'https://api.bilibili.com/x/web-interface/view', 
    params={
      'aid': aid,
      'bvid': bvid
    },
    headers=headers,
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
  cid = res['cid']
  p_url = ''
  p_tip = ''
  if p > 1:
    p_url = '?p=' + str(p)
    p_tip = ' P' + str(p)
    for i in res['pages']:
      if i['page'] == p:
        cid = i['cid']
  logger.info(f'{bvid} av{aid} P{p} cid: {cid}')
  title = (
    res['title']
    .replace('&', '&gt;')
    .replace('<', '&lt;')
    .replace('>', '&gt;')
  )
  msg = (
    f"<a href=\"https://www.bilibili.com/video/{bvid}{p_url}\">{title}{p_tip}</a> - "
    f"<a href=\"https://space.bilibili.com/{res['owner']['mid']}\">{res['owner']['name']}</a>"
  )
  
  try:
    data = util.Videos()
    key = bvid
    if p > 1:
      key += '_p' + str(p)
    if not (info := data.get(key, None)) or nocache:
      info = await getVideo(bvid, aid, cid)
    video, duration, width, height, thumbnail = tuple(info)
      
    m1 = await bot.send_video(
      video=video,
      duration=int(duration),
      width=int(width),
      height=int(height),
      thumbnail=thumbnail,
      supports_streaming=True,
      caption=msg, 
      has_spoiler=mark,
      chat_id=message.chat.id,
      reply_to_message_id=message.message_id,
      parse_mode="HTML",
      read_timeout=60,
      write_timeout=60,
      connect_timeout=60,
      pool_timeout=60,
    )
    v = m1.video
    data[key] = [v.file_id, v.duration, v.width, v.height, v.thumbnail.file_id]
    data.save()
  except Exception:
    logger.error(traceback.print_exc())
    await bot.send_message(
      text='媒体发送失败', 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  await bot.delete_message(chat_id=message.chat.id, message_id=mid.message_id)
