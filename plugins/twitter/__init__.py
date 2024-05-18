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
    InputMediaDocument,
)
from telegram.ext import ContextTypes
import traceback
import ujson as json
from uuid import uuid4

import config
import util
from util.log import logger
from plugin import handler, inline_handler

from .data_source import parseText, get_twitter, parseTidMsg, parseMedias
from .getPreview import getPreview


@handler('tid',
  private_pattern=r"^((https?://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?\d{13,}(.*)$",
  pattern=r"^((tid|Tid|TID) ?)((https?://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?\d{13,}(.*)$",
  info="获取推文 /tid <url/tid> [hide] [mark]"
)
async def tid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    tid, hide, mark = parseText(text)
    logger.info(f"{tid = }, {hide = }, {mark = }")
    
    if tid == "":
        return await update.message.reply_text(
            "用法: /tid <url/tid> [hide] [mark]\n"
            "tid/url: 推文链接或status_id\n"
            "hide: 隐藏信息，推文内容将只显示推文链接\n"
            "mark: 添加遮罩\n"
            "私聊小派魔时可以省略/tid，直接发送<url/tid> [hide] [mark]哦\n"
            "或者使用@hbcao1bot <url/tid> [hide] [mark]作为内联模式发送~",
            reply_to_message_id=update.message.message_id,
        )

    res = await get_twitter(tid)
    if type(res) == str:
        return await update.message.reply_text(res)
    if 'tombstone' in res.keys():
        logger.info(json.dumps(res))
        return await update.message.reply_text(res['tombstone']['text']['text'])
    
    msg, full_text, time = parseTidMsg(res) 
    msg = msg if not hide else 'https://x.com/i/status/' + tid
    tweet = res["legacy"]
    '''
    if "extended_entities" not in tweet:
        return await update.message.reply_text(msg, parse_mode='HTML')
    '''
    # 格式化媒体
    medias = parseMedias(tweet)
    ms = []
    videos = util.getData('videos')
    for media in medias:
      if media["type"] == "photo":
        url = media["url"]
        md5 = media['md5']
        img = await util.getImg(
          url, 
          headers=config.twitter_headers,
          saveas=f"{md5}.png"
        )
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
        if not (video := videos.get(md5, None)):
          img = await util.getImg(
            url, 
            headers=config.twitter_headers, 
            saveas=f"{md5}.mp4"
          )
          video = open(img, 'rb')
        add = InputMediaVideo(
          media=video,
          caption=msg if len(ms) == 0 else None,
          parse_mode="HTML",
          has_spoiler=mark,
        )
        ms.append(add)
    
    flag = False
    try:
      img = await getPreview(res, medias, full_text, time)
    except Exception:
      logger.warning(traceback.format_exc())
    else: 
      flag = True
      #ms[0]._unfreeze()
      #ms[0].caption = None
      add = InputMediaPhoto(
        media=open(img, 'rb'),
        #caption=msg,
        #parse_mode="HTML",
        has_spoiler=mark,
      )
      ms = [add] + ms
      
    # 发送
    try:
      m = await update.message.reply_media_group(
        media=ms, 
        reply_to_message_id=update.message.message_id,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60,
        pool_timeout=60,
      )
      if flag:
        m = m[1:]
      for i, ai in enumerate(m):
        md5 = medias[i]['md5']
        #if getattr(ai, 'photo', None) and not photos.get(md5s[i], None):
        #  photos[md5s[i]] = ai.photo[-1].file_id
        
        if getattr(ai, 'video', None) and not videos.get(md5, None):
          videos[md5] = ai.video.file_id
      # util.setData('photos', photos)
      util.setData('videos', videos)
    except Exception:
      logger.info(msg)
      logger.info(json.dumps(res))
      logger.warning(traceback.format_exc())
      await update.message.reply_text("媒体发送失败")


@inline_handler(r"^(https://(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?((tid|Tid|TID) ?)?\d{13,}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$")
async def _(update, context, text):
  results = []
  tid, hide, mark = parseText(text)
  logger.info(f"{tid = }, {hide = }, {mark = }")
  if tid == "":
      return

  res = await get_twitter(tid)
  if type(res) == str:
      logger.info(res)
      return await update.inline_query.answer([])

  tweet = res["legacy"]
  msg, full_text, time = parseTidMsg(res)
  msg = msg if not hide else 'https://x.com/i/status/' + tid 
  medias = parseMedias(tweet)
  
  count = 0
  try:
    img = await getPreview(res, medias, full_text, time)
    m = await context.bot.send_photo(
      chat_id=config.echo_chat_id,
      photo=open(img, 'rb'),
    )
    await context.bot.delete_message(
      chat_id=config.echo_chat_id,
      message_id=m.message_id
    )
    photo_file_id = m.photo[-1].file_id
  except Exception:
    logger.warning(traceback.format_exc())
  else: 
    count += 1
    results.append(
        InlineQueryResultCachedPhoto(
            id=str(uuid4()),
            photo_file_id=photo_file_id,
            caption=msg,
            parse_mode="HTML",
        )
    )
  
  if len(medias) > 0:
      for media in medias:
          if media["type"] == "photo":
              count += 1
              results.append(
                  InlineQueryResultPhoto(
                      id=str(uuid4()),
                      photo_url=media["url"],
                      thumbnail_url=media["thumbnail_url"],
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
                      title=msg,
                      mime_type="video/mp4",
                      caption=msg,
                      parse_mode="HTML",
                      description=f'最佳质量(bitrate: {variants[0]["bitrate"]}, 若预览图为空，请勿选择)',
                  )
              )
              
              if len(variants) >= 2:
                  results.append(
                      InlineQueryResultVideo(
                          id=str(uuid4()),
                          video_url=variants[1]["url"],
                          title=msg,
                          mime_type="video/mp4",
                          thumbnail_url=media["thumbnail_url"],
                          caption=msg,
                          parse_mode="HTML",
                          description=f'较高质量(bitrate: {variants[1]["bitrate"]})',
                      )
                  )
  else:
      count += 1
      results.append(
          InlineQueryResultArticle(
              id=str(uuid4()),
              title=msg,
              input_message_content=InputTextMessageContent(
                  msg, parse_mode="HTML"
              ),
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
  