import traceback
from telegram import (
  Update,
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  InlineQueryResultPhoto,
  InlineQueryResultsButton,
  InputMediaPhoto,
  InputMediaDocument,
)

import config
import util
from util.log import logger
from util.progress import Progress
from plugin import handler, inline_handler, button_handler

from .data_source import parseText, parsePidMsg, getAnime


_end = r'/?(\?.*)?(#.*)?( .*)?$'
@handler('pid', 
  private_pattern=r"((^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12})|"
                  r"(^((https?://)?(www.)?pixiv.net/(artworks|i)/)?\d{6,12}))" + _end,
  pattern=r"((^((pid|Pid|PID) ?)(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12})|"
          r"(^((pid|Pid|PID) ?)((https?://)?(www.)?pixiv.net/(artworks|i)/)?\d{6,12}))/?(\?.*)?(#.*)?$",
  info="获取p站作品 /pid <url/pid> [hide] [mark]"
)
async def _pixiv(update, context, text=None):
  pid, hide, mark, origin = parseText(text)
  if pid == "":
    return await update.message.reply_text(
        "用法: /pid <url/pid> [hide/省略] [mark/遮罩] [origin/原图]\n"
        "url/pid: p站链接或pid\n"
        "[hide/省略]: 省略图片说明\n"
        "[mark/遮罩]: 给图片添加遮罩\n"
        "[origin/原图]: 发送原图\n"
        "私聊小派魔时可以省略/tid，直接发送<url/pid>哦\n"
        "或者使用@hbcao1bot <url/pid>作为内联模式发送~",
        reply_to_message_id=update.message.message_id,
    )
    
  message = update.message
  bot = context.bot
  
  mid = await message.reply_text(
    "请等待...",
    reply_to_message_id=update.message.message_id,
  )
  try:
    url = f"https://www.pixiv.net/ajax/illust/{pid}"
    r = await util.get(url, headers=config.pixiv_headers)
  except Exception:
    return await update.message.reply_text(
        "连接超时",
        reply_to_message_id=update.message.message_id,
    )
  res = r.json()
  if res["error"]:
    return await update.message.reply_text(
      '错误: ' + res["message"],
      reply_to_message_id=update.message.message_id,
    )
    
  res = res['body']
  msg = parsePidMsg(res, hide)
  if res['illustType'] == 2:
    origin = False
    await message.reply_chat_action(action='upload_video')
    animations = util.Data('animations')
    if not (info := animations[pid]):
      anime = await getAnime(pid)
      if not anime:
        return await message.reply_text(
          '生成动图失败',
          reply_to_message_id=update.message.message_id,
        )
      info = util.videoInfo(anime)
    animation, duration, width, height, thumbnail = tuple(info)
    m = await message.reply_animation(
      animation=animation,
      duration=duration,
      width=width,
      height=height,
      thumbnail=thumbnail,
      caption=msg,
      parse_mode='HTML',
      has_spoiler=mark,
      reply_to_message_id=update.message.message_id,
    )
    v = m.animation
    animations[pid] = [v.file_id, v.duration, v.width, v.height, v.thumbnail.file_id]
    animations.save()
    await bot.delete_message(
      chat_id=message.chat.id, message_id=mid.message_id
    )
  else:
  
    imgUrl = res["urls"]["original"]
    count = res["pageCount"]
    piece = 10
    pcount = (count - 1) // piece + 1
      
    for p in range(pcount):
      await update.message.reply_chat_action(action='upload_photo')
      bar = Progress(
        bot, mid, 
        "正在获取 p" + f"{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}",
      )
      ms = []
      documents = util.Documents()
      i = p * piece
      while i < min((p + 1) * piece, count):
        url = imgUrl.replace("_p0", f"_p{i}")
        name = f"{pid}_p{i}"
        tip = (
          f"\n{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}"
          if p > 0
          else ""
        )
        if not (origin and (media := documents[name])):
          try:
            img = await util.getImg(
              url, 
              saveas=name, 
              ext=True, 
              headers=config.pixiv_headers, 
            )
            util.resizePhoto(img, saveas=img)
            media = open(img, 'rb')
          except Exception:
            logger.warning(traceback.format_exc())
            return await update.message.reply_text(
              tip + "图片获取失败",
              reply_to_message_id=update.message.message_id,
            )
          else:
            bar.add(90 // min(piece, count - p * piece))
        
        caption = None
        if len(ms) == 0:
          caption = msg if p == 0 else tip
        
        if not origin:
          ms.append(
            InputMediaPhoto(
              media=media,
              caption=caption,
              parse_mode="HTML",
              has_spoiler=mark,
            )
          )
        else:
          ms.append(
            InputMediaDocument(
              media=media,
              caption=caption,
              parse_mode="HTML",
            )
          )
        i += 1
  
      try:
        m = await update.message.reply_media_group(
          media=ms,
          reply_to_message_id=update.message.message_id,
          read_timeout=120,
          write_timeout=120,
          connect_timeout=120,
          pool_timeout=120,
        )
        if origin:
          for i in range(0, min(piece, count - p * piece)):
            ii = p * piece + i
            name = f"{pid}_p{ii}"
            documents[name] = m[i].document.file_id
          documents.save()
      except Exception:
        logger.warning(traceback.format_exc())
        logger.info(msg)
        await update.message.reply_text(
          tip + "发送失败",
          reply_to_message_id=update.message.message_id,
        )
  
      await bot.delete_message(
        chat_id=update.message.chat_id, message_id=mid.message_id
      )
      if p < pcount - 1:
        mid = await update.message.reply_text(
            "请等待...",
            reply_to_message_id=update.message.message_id,
        )
  
  keyboard = [[]]
  if not origin:
    if res['illustType'] != 2:
      keyboard[0].append(InlineKeyboardButton(
        "获取原图", 
        callback_data=f"{pid} {'hide' if hide else ''} origin"
      ))
    if not mark:
      keyboard[0].append(InlineKeyboardButton(
        "添加遮罩", 
        callback_data=f"{pid} {'hide' if hide else ''} mark"
      ))
  
  keyboard[0].append(
    InlineKeyboardButton("详细描述" if hide else "简略描述", callback_data=f"{pid} {'hide' if not hide else ''} {'origin' if origin else ''}")
  )
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
    "获取完成", 
    reply_to_message_id=update.message.message_id,
    reply_markup=reply_markup,
  )
  
  
@button_handler(pattern=r"^\d{6,12}")
async def _(update, context, query):
  # logger.info(update)
  message = update.callback_query.message
  _update = Update(
    update_id=update.update_id, 
    message=message, 
    callback_query=update.callback_query
  )
  await message.edit_reply_markup(reply_markup=None)
  await _pixiv(_update, context, query.data)
  