import re
import traceback
from telegram import (
  Update,
  LinkPreviewOptions,
  InputMediaPhoto,
  InputMediaDocument,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
)
import os

import config
import util
from util.log import logger
from plugin import handler, button_handler

from .data_source import parseKidMsg, parsePage


private_pattern = r"(?:(?:https://)?kemono\.(?:party|su)/)?([a-z]+)(?:(?:/user)?/(\d+))?(?:/post)?/(\d+)"
@handler('kid',
  private_pattern="^"+private_pattern,
  pattern="^kid " + private_pattern,
  info="kenomo爬取 /kid <url>"
)
async def kid(update, context, text):
  text: str = update.message["text"] if text is None else text
  arr = text.split(' ')
  nocache = False
  mark = False
  if 'nocache' in arr: nocache = True
  if 'mark' in arr: mark = True
 
  if not (match := re.match(private_pattern, text)):
    return await update.message.reply_text(
      "用法: /kid <url>"
    )
  message = update.message
  bot = context.bot
  
  source = match.group(1)
  uid = match.group(2)
  _kid = match.group(3)
  #logger.info(_kid)
  arr = _kid.split('/')
  kid = f'https://kemono.su/{source}'
  if uid: kid += f'/user/{uid}'
  kid += f'/post/{_kid}' 
  mid = await message.reply_text(
    "请等待...", reply_to_message_id=update.message.message_id
  )
  r = await util.get(kid)
  if r.status_code != 200:
    return await message.reply_text(
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
  
  # uid = user_url.split('/')[-1]
  # if source == 'fanbox' and len(files) > 1:
  #  files = files[1:]
    
  if len(files) > 10:
    key = f'kemono/{source}/{_kid}'
    with util.Data('urls') as data:
      if not (url := data[key]) or nocache:
        url = await parsePage(title, files, nocache)
    
    msg = (
      f'标题: {title}\n'
      f'作者: <a href="{user_url}">{user_name}</a>\n'
      f'预览: {url}\n'
      f'原链接: {kid}'
    )
    if attachments:
      msg += '\n' + attachments
    await message.reply_text(
      text=msg,
      reply_to_message_id=update.message.message_id,
      parse_mode="HTML",
      link_preview_options=LinkPreviewOptions(
        url=url,
        prefer_large_media=True,
        show_above_text=False,
      ),
    )
    await bot.delete_message(
      chat_id=update.message.chat_id, 
      message_id=mid.message_id,
    )
    return
  
  await message.reply_chat_action(action='upload_photo')
  msg = (
    f'<a href="{kid}">{title}</a> - '
    f'<a href="{user_url}">{user_name}</a>'
  )
  if attachments:
    msg += '\n' + attachments
    
  ms = []
  for i, ai in enumerate(files):
    caption = None
    if i == 0:
      caption = msg
    url = ai['thumbnail']
    ext = os.path.splitext(url)[-1]
    if ext == '.gif':
      url = ai['url']
    img = await util.getImg(
      url, 
      saveas=f'{source}_{_kid}_p{i}',
      ext=True,
    )
    if ext != '.gif':
      img = util.resizePhoto(img)
      media = util.img2bytes(img, ext)
      ms.append(InputMediaPhoto(
        media=media,
        caption=caption,
        parse_mode="HTML",
        has_spoiler=mark,
      ))
    else:
      media = open(img, 'rb')
      ms.append(InputMediaDocument(
        media=media,
        caption=caption,
        parse_mode="HTML",
      ))
      
  try:
    m = await message.reply_media_group(
      media=ms,
      reply_to_message_id=update.message.message_id,
      read_timeout=120,
      write_timeout=120,
      connect_timeout=120,
      pool_timeout=120,
    )
  except:
    logger.warning(traceback.format_exc())
    await message.reply_text(
      "发送失败",
      reply_to_message_id=update.message.message_id,
    )
    
  await bot.delete_message(
    chat_id=update.message.chat_id, 
    message_id=mid.message_id,
  )
  
  keyboard = [[]]
  if not mark:
    keyboard[0].append(
      InlineKeyboardButton("添加遮罩", callback_data=f"{source}/{_kid} mark")
    )
  reply_markup = InlineKeyboardMarkup(keyboard)
  mid = await message.reply_text(
    "获取完成", 
    reply_to_message_id=update.message.message_id,
    reply_markup=reply_markup,
  )
  
  
@button_handler(pattern=r"([a-z]+)/(\d+)")
async def _(update, context, query):
  # logger.info(update)
  message = update.callback_query.message
  _update = Update(
    update_id=update.update_id, 
    message=message, 
    callback_query=update.callback_query
  )
  await message.edit_reply_markup(reply_markup=None)
  await kid(_update, context, query.data)
  