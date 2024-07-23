import re
import os.path
import traceback
import asyncio
from telegram import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  InputMediaPhoto,
  InputMediaDocument,
  LinkPreviewOptions,
)
from datetime import datetime

import util
from util.log import logger
from plugin import handler, button_handler
from .data_source import PluginException, get_post, parseMsg, parseMedias


_pattern = r'(?:fanbox ?)?(?:https?://)?(?:[a-z0-9]+\.)?fanbox\.cc/(?:[@a-z0-9]+/)?posts/(\d+)'
@handler('fanbox', 
  private_pattern=_pattern,
  pattern='^' + _pattern,
  info="获取fanbox作品 /fanbox <url/postId> [hide] [mark]"
)
async def _fanbox(update, context, text=None):
  logger.info(text)
  if not (match := re.search(_pattern, text)):
    return await update.message.reply_text(
      "用法: /fanbox <url/postId> [hide/省略] [mark/遮罩] [origin/原图]\n"
      "url/postId: fanbox链接或postId\n",
      reply_to_message_id=update.message.message_id,
    )
  pid = match.group(1)
  
  hide = False
  mark = False
  origin = False
  arr = text.split(" ")
  if "hide" in arr or '省略' in arr: 
    hide = True
  if "mark" in arr or '遮罩' in arr: 
    mark = True
  if 'origin' in arr or '原图' in arr: 
    origin = True
  logger.info(f"{pid = }, {hide = }, {mark = }, {origin = }")
  
  message = update.message
  bot = context.bot
  
  mid = await message.reply_text(
    "请等待...",
    reply_to_message_id=message.message_id,
  )
  
  try:
    res = await get_post(pid)
  except PluginException as e:
    return await message.reply_text(
      '错误: ' + str(e),
      reply_to_message_id=message.message_id,
    )
  
  msg = parseMsg(res)
  medias = parseMedias(res)
  
  if res['coverImageUrl']:
    img = await util.getImg(res['coverImageUrl'])
    await message.reply_photo(
      open(img, 'rb'),
      caption=msg,
      reply_to_message_id=message.message_id,
      parse_mode='HTML',
    )
    await bot.delete_message(chat_id=mid.chat.id, message_id=mid.message_id)
    mid = await message.reply_text(
      "请等待...",
      reply_to_message_id=message.message_id,
    )
  elif len(medias) == 0:
    await message.reply_text(
      msg,
      reply_to_message_id=message.message_id,
      parse_mode='HTML',
    )
  if res['feeRequired'] > 0:
    await bot.delete_message(chat_id=mid.chat.id, message_id=mid.message_id)
    return await message.reply_text(
      f"该投稿为付费内容 ({res['feeRequired']}日圓)",
      reply_to_message_id=message.message_id,
    )
  
  try:
    if len(medias) < 11: 
      await send_photos(update, medias, msg, hide, mark, origin)
    else:
      url, msg = await get_telegraph(res, medias)
      await bot.delete_message(chat_id=mid.chat.id, message_id=mid.message_id)
      return await message.reply_text(
        text=msg,
        parse_mode='HTML',
        reply_to_message_id=message.message_id,
        link_preview_options=LinkPreviewOptions(
          url=url,
          prefer_large_media=True,
          show_above_text=False,
        ),
      )
  except PluginException:
    return
  
  await context.bot.delete_message(
    chat_id=mid.chat.id,
    message_id=mid.message_id,
  )
  
  if str(message.chat.type) != "private":
    return
  keyboard = [[
    InlineKeyboardButton(
      "获取原图" if not origin else '取消原图', 
      callback_data=(
        f"fanbox {pid}"
        f" {'hide' if hide else ''}"
        f" {'origin' if not origin else ''}"
      ),
    ),
    InlineKeyboardButton(
      "添加遮罩" if not mark else '取消遮罩', 
      callback_data=(
        f"fanbox {pid}"
        f" {'hide' if hide else ''}"
        f" {'mark' if not mark else ''}"
      ),
    ),
    InlineKeyboardButton(
      "详细描述" if hide else "简略描述", 
      callback_data=(
        f"fanbox {pid}"
        f" {'hide' if not hide else ''}"
        f" {'mark' if mark else ''}"
        f" {'origin' if origin else ''}"
      ),
    ),
  ]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  await message.reply_text(
    "获取完成", 
    reply_to_message_id=message.message_id,
    reply_markup=reply_markup,
  )
  
  
@button_handler(pattern=r"^fanbox")
async def _(update, context, query):
  logger.info(update)
  message = update.callback_query.message
  _update = Update(
    update_id=update.update_id, 
    message=message, 
    callback_query=update.callback_query
  )
  await message.edit_reply_markup(reply_markup=None)
  await _fanbox(_update, context, query.data)
  
  
async def send_photos(update, medias, msg, hide, mark, origin):
  data = util.Documents() if origin else util.Photos()
  
  async def get_img(i):
    nonlocal origin, data
    url = medias[i]['url']
    name = medias[i]['name']
    ext = medias[i]['ext']
    if not origin:
      url = medias[i]['thumbnail']
      name += '_thumbnail'
    if media := data[name]:
      return media
      
    try:
      headers={
        'origin': 'https://www.fanbox.cc',
        'referer': 'https://www.fanbox.cc/',
      }
      img = await util.getImg(url, saveas=name, ext=ext, headers=headers)
      if not origin:
        ext = os.path.splitext(img)[-1]
        img = util.resizePhoto(img)
        media = util.img2bytes(img, ext)
      else:
        media = open(img, 'rb')
      return media
    except Exception:
      logger.error(traceback.format_exc())
      await update.message.reply_text(
        "图片获取失败",
        reply_to_message_id=message.message_id
      )
      raise PluginException('图片获取失败')
      
  tasks = [get_img(i) for i in range(len(medias))]
  result = await asyncio.gather(*tasks)
  ms = []
  t = InputMediaDocument if origin else InputMediaPhoto
  
  kwargs = {}
  if not origin:
    kwargs['has_spoiler'] = mark
  
  k = kwargs.copy()
  k.update({
    'media': result[0],
    'caption': msg, 
    'parse_mode': 'HTML',
  })
  ms.append(t(**k))
  for i in result[1:]:
    k = kwargs.copy()
    k['media'] = i
    ms.append(t(**k))
    
  await update.message.reply_chat_action(action='upload_photo')
  
  try:
    m = await update.message.reply_media_group(
      media=ms,
      reply_to_message_id=update.message.message_id,
      read_timeout=120,
      write_timeout=120,
      connect_timeout=120,
      pool_timeout=120,
    )
    
    for i in range(len(medias)):
      name = medias[i]['name']
      if not origin:
        name += '_thumbnail'
      tt = m[i].document if origin else m[i].photo[-1]
      data[name] = tt.file_id
    data.save()
  except Exception:
    logger.warning(traceback.format_exc())
    raise PluginException('图片发送错误')
  

async def get_telegraph(res, medias):
  data = util.Data('urls')
  now = datetime.now()
  pid = res['id']
  key = f'{pid}-{now:%m-%d}'
  if not (url := data[key]):
    content = []
    for i in medias:
      content.append({
        'tag': 'img',
        'attrs': {
          'src': i['url'],
        },
      })
   
    url = await util.telegraph.createPage(f"[fanbox] {pid} {res['title']}", content)
    data[key] = url
    data.save()
    
  msg = (
    f"标题: {res['title']}\n"
    f"预览: {url}\n"
    f"作者: <a href=\"https://{res['creatorId']}.fanbox.cc/\">{res['user']['name']}</a>\n"
    f"数量: {len(medias)}\n"
    f"原链接: https://{res['creatorId']}.fanbox.cc/posts/{pid}"
  )
  return url, msg
  