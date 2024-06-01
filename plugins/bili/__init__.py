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

import config
import util
from util.log import logger
from plugin import handler, inline_handler, button_handler
from .data_source import getVideo


_pattern = r"(?:^|bilibili\.com/video/)(av\d{1,11}|BV[0-9a-zA-Z]{8,12})|(?:b23\.tv\\?/((?![0-9]{7,7})[0-9a-zA-Z]{7,7}))"
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
  
  arr = text.split(' ')
  nocache = False
  if 'nocache' in arr:
    nocache = True
  
  match = re.search(_pattern, text)
  if match.group(2):
    r = httpx.get('https://b23.tv/'+ match.group(2), headers=config.bili_headers, follow_redirects=True)
    text = str(r.url).split('?')[0]
    match = re.search(_pattern, text)
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
    data = util.Videos()
    # logger.info(data)
    logger.info(f'bvid: {bvid} video: '+str(data.get(bvid, None)))
    
    if not (info := data.get(bvid, None)) or nocache:
      info = await getVideo(bvid, aid, res['cid'])
    else:
      info = info.split('/')
    video, duration, width, height, thumbnail = tuple(info)
      
    m1 = await bot.send_video(
      video=video,
      duration=int(duration),
      width=int(width),
      height=int(height),
      thumbnail=thumbnail,
      supports_streaming=True,
      caption=msg, 
      chat_id=message.chat.id,
      reply_to_message_id=message.message_id,
      parse_mode="HTML",
      read_timeout=60,
      write_timeout=60,
      connect_timeout=60,
      pool_timeout=60,
    )
    v = m1.video
    vv = map(str, [v.file_id, v.duration, v.width, v.height, v.thumbnail.file_id])
    data[bvid] = '/'.join(vv)
    data.save()
  except Exception:
    logger.error(traceback.print_exc())
    await bot.send_message(
      text='媒体发送失败', 
      chat_id=message.chat.id, 
      reply_to_message_id=message.message_id,
    )
  await bot.delete_message(chat_id=message.chat.id, message_id=m.message_id)
    