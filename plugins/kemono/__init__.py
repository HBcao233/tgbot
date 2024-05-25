import re
import traceback
from telegram import (
  Update,
  LinkPreviewOptions,
)

import config
import util
from util.log import logger
from plugin import handler, button_handler

from .data_source import parseKidMsg, parsePage


private_pattern = r"(?:(?:https://)?kemono\.(?:party|su)/)?([^/]+)(?:/user)?/(\d+)(?:/post)?/(\d+)"
@handler('kid',
  private_pattern="^"+private_pattern,
  pattern="^kid " + private_pattern,
  info="kenomo爬取 /kid <url>"
)
async def kid(update, context, text):
  text: str = update.message["text"] if text is None else text
  arr = text.split(' ')
  nocache = False
  if 'nocache' in arr:
    nocache = True
  
  if not (match := re.match(private_pattern, text)):
      return await update.message.reply_text(
        "用法: /kid <url>"
      )
  bot = context.bot
  
  source = match.group(1)
  uid = match.group(2)
  _kid = match.group(3)
  #logger.info(_kid)
  arr = _kid.split('/')
  kid = f'https://kemono.su/{source}/user/{uid}/post/{_kid}' 
  mid = await update.message.reply_text(
      "请等待...", reply_to_message_id=update.message.message_id
  )
  r = await util.get(kid)
  if r.status_code != 200:
    return await update.reply_text(
        reply_to_message_id=mid.message_id,
        text='请求失败',
    )
  try:
    title, user_name, user_url, attachments, files = parseKidMsg(kid, r.text)
  except Exception as e:
    logger.warning(traceback.format_exc())
    return await bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=mid.message_id,
        text=str(e),
    )
    
  if 'fanbox' in _kid and len(files) > 1:
    files = files[1:]
  
  key = f'kemono/{source}/{uid}/{_kid}'
  with util.Data('urls') as data:
    if not (url := data[key]) or nocache:
      url = await parsePage(title, files, nocache)
  
  msg = (
    f'标题: {title}\n'
    f'作者: <a href="{user_url}">{user_name}</a>\n'
    f'预览: {url}'
  )
  if attachments:
    msg += '\n' + attachments
  await update.message.reply_text(
    text=msg,
    reply_to_message_id=update.message.message_id,
    parse_mode="HTML",
    link_preview_options=LinkPreviewOptions(
      url=url,
      prefer_large_media=True,
      show_above_text=False,
    ),
  )
  await context.bot.delete_message(
    chat_id=update.message.chat_id, message_id=mid.message_id
  )
    