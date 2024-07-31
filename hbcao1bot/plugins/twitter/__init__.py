from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedPhoto,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InlineQueryResultsButton,
    InputTextMessageContent,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import ContextTypes
import traceback
import ujson as json
from uuid import uuid4
import re

import config
import util
from util.log import logger
from plugin import handler, inline_handler, button_handler

from .data_source import headers, get_twitter, parseTidMsg, parseMedias


_pattern = r'(?:^|^(?:tid|Tid|TID) ?|(?:https?://)?(?:twitter|x|vxtwitter|fxtwitter)\.com/[a-zA-Z0-9_]+/status/)(\d{13,})(?:[^0-9].*)?$'
@handler('tid',
  private_pattern=_pattern,
  pattern=_pattern.replace(r'(?:^|', r'(?:'),
  info="获取推文 /tid <url/tid> [hide] [mark]"
)
async def _tid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
  message = update.message
  if not (match := re.search(_pattern, text)):
    return await message.reply_text(
      "用法: /tid <url/tid> [hide] [mark]\n"
      "tid/url: 推文链接或status_id\n"
      "hide: 隐藏信息，推文内容将只显示推文链接\n"
      "mark: 添加遮罩\n"
      "私聊小派魔时可以省略/tid，直接发送<url/tid> [hide] [mark]哦\n"
      "或者使用@hbcao1bot <url/tid> [hide] [mark]作为内联模式发送~",
      reply_to_message_id=message.message_id,
    )
  tid = match.group(1)
  hide = False
  mark = False
  arr = text.split(" ")
  if "hide" in arr:
    hide = True
  if "mark" in arr or '遮罩' in arr:
    mark = True
  logger.info(f"{tid = }, {hide = }, {mark = }")
  
  res = await get_twitter(tid)
  if type(res) == str:
      return await message.reply_text(res)
  if 'tombstone' in res.keys():
      logger.info(json.dumps(res))
      return await message.reply_text(res['tombstone']['text']['text'])
  
  msg, full_text, time = parseTidMsg(res) 
  msg = msg if not hide else 'https://x.com/i/status/' + tid
  tweet = res["legacy"]
  
  await message.reply_chat_action(action='upload_photo')
  # 格式化媒体
  medias = parseMedias(tweet)
  if len(medias) == 0:
    return await message.reply_text(
      msg,
      parse_mode='HTML',
      reply_to_message_id=message.message_id
    )
    
  ms = []
  videos = util.Data('videos')
  for media in medias:
    if media["type"] == "photo":
      url = media["url"]
      md5 = media['md5']
      img = await util.getImg(url, headers=headers, ext=True)
      photo = open(img, 'rb')
      add = InputMediaPhoto(
        media=photo,
        caption=msg if len(ms) == 0 else None,
        parse_mode="HTML",
        has_spoiler=mark,
      )
      ms.append(add)
    else:
      url = media["url"]
      md5 = media['md5']
      if not (info := videos.get(md5, None)):
        path = await util.getImg(
          url, 
          headers=headers, 
          ext="mp4"
        )
        info = util.videoInfo(path)
      video, duration, width, height, thumbnail = tuple(info)
      add = InputMediaVideo(
        media=video,
        caption=msg if len(ms) == 0 else None,
        parse_mode="HTML",
        has_spoiler=mark,
        duration=int(duration),
        width=int(width),
        height=int(height),
        thumbnail=thumbnail,
        supports_streaming=True,
      )
      ms.append(add)
  
  # 发送
  try:
    m = await message.reply_media_group(
      media=ms, 
      reply_to_message_id=message.message_id,
      read_timeout=60,
      write_timeout=60,
      connect_timeout=60,
      pool_timeout=60,
    )
    for i, ai in enumerate(m):
      md5 = medias[i]['md5']
      #if getattr(ai, 'photo', None) and not photos.get(md5s[i], None):
      #  photos[md5s[i]] = ai.photo[-1].file_id
      
      if getattr(ai, 'video', None) and not videos.get(md5, None):
        v = ai.video
        videos[md5] = [v.file_id, v.duration, v.width, v.height, v.thumbnail.file_id]
    # util.setData('photos', photos)
    videos.save()
  except Exception:
    logger.info(msg)
    logger.info(json.dumps(res))
    logger.warning(traceback.format_exc())
    await update.message.reply_text("媒体发送失败")
  
  if str(message.chat.type) != "private":
    return
  keyboard = [[]]
  if not mark:
    keyboard[0].append(InlineKeyboardButton(
      "添加遮罩", 
      callback_data=f"tid {tid} {'hide' if hide else ''} mark"
    ))
  keyboard[0].append(InlineKeyboardButton(
    "详细描述" if hide else "简略描述", 
    callback_data=f"tid {tid} {'hide' if not hide else ''} {'mark' if mark else ''}"
  ))
  reply_markup = InlineKeyboardMarkup(keyboard)
  mid = await message.reply_text(
    "获取完成", 
    reply_to_message_id=update.message.message_id,
    reply_markup=reply_markup,
  )
  '''
  if str(message.chat.type) != "private":
    async def _del(context):
      await context.bot.delete_message(chat_id=context.job.data[0], message_id=context.job.data[1])
 
    context.job_queue.run_once(
      _del, 10, 
      data=[mid.chat.id, mid.message_id],
    )
  '''
  
  
@button_handler(pattern=r"^tid \d{13,}")
async def _(update, context, query):
  # logger.info(update)
  message = update.callback_query.message
  _update = Update(
    update_id=update.update_id, 
    message=message, 
    callback_query=update.callback_query
  )
  await message.edit_reply_markup(reply_markup=None)
  await _tid(_update, context, query.data)
  

@inline_handler(r"^(https://(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?((tid|Tid|TID) ?)?\d{13,}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$")
async def _(update, context, text):
  if not (match := re.search(_pattern, text)):
    return await update.inline_query.answer()
  tid = match.group(1)
  hide = False
  mark = False
  arr = text.split(" ")
  if "hide" in arr:
    hide = True
  if "mark" in arr or '遮罩' in arr:
    mark = True
  logger.info(f"{tid = }, {hide = }, {mark = }")
    
  results = []
  res = await get_twitter(tid)
  if type(res) == str:
      logger.warning(res)
      return await update.inline_query.answer()

  tweet = res["legacy"]
  msg, full_text, time = parseTidMsg(res)
  msg = msg if not hide else 'https://x.com/i/status/' + tid 
  medias = parseMedias(tweet)
  
  count = 0
  if len(medias) == 0:
    count = 1
    results.append(
      InlineQueryResultArticle(
        id=str(uuid4()),
        title=msg,
        input_message_content=InputTextMessageContent(
            msg, parse_mode="HTML"
        ),
      )
    )
  else:
    for media in medias:
      if media["type"] == "photo":
        count += 1
        results.append(
          InlineQueryResultPhoto(
            id=str(uuid4()),
            photo_url=media["url"],
            thumbnail_url=media["thumbnail_url"],
            title=count+1,
            description=msg,
            caption=msg,
            parse_mode="HTML",
          )
        )
      else:
        count += 1
        variants = media['variants']
        results.append(
          InlineQueryResultVideo(
            id=str(uuid4()),
            video_url=media["url"],
            thumbnail_url=media["thumbnail_url"],
            mime_type="video/mp4",
            caption=msg,
            parse_mode="HTML",
            title=count+1,
            description=f'最佳质量(bitrate: {variants[0]["bitrate"]}, 若预览图为空，请勿选择)',
          )
        )
        
        if len(variants) >= 2:
          results.append(
            InlineQueryResultVideo(
              id=str(uuid4()),
              video_url=variants[1]["url"],
              mime_type="video/mp4",
              thumbnail_url=media["thumbnail_url"],
              caption=msg,
              parse_mode="HTML",
              title=f'{count+1}-2',
              description=f'较高质量(bitrate: {variants[1]["bitrate"]})',
            )
          )
    
      
  countFlag = count > 1
  btn_text = "获取" + ("遮罩" if mark else "全部") + ("(隐藏描述)" if hide else "")
  start_parameter = f"{tid}_{'hide' if hide else ''}_{'mark' if mark else ''}" 
  logger.info(f"btn_text: {btn_text}, start: {start_parameter}")
  
  button = InlineQueryResultsButton(
      text=btn_text,
      start_parameter=start_parameter,
  ) if countFlag or mark else None
  await update.inline_query.answer(
      results,
      cache_time=10,
      button=button,
  )
  