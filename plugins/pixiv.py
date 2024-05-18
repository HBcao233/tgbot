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

import config
import util
from util.log import logger
from plugin import handler, inline_handler, button_handler
    

_end = r'/?(\?.*)?(#.*)?$'
@handler('pid', 
  private_pattern=r"((^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12})|"
                  r"(^((https?://)?(www.)?pixiv.net/(artworks|i)/)?\d{6,12}))" + _end,
  pattern=r"((^((pid|Pid|PID) ?)(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12})|"
          r"(^((pid|Pid|PID) ?)((https?://)?(www.)?pixiv.net/(artworks|i)/)?\d{6,12}))/?(\?.*)?(#.*)?$",
  info="获取p站作品 /pid <url/pid> [hide] [mark]"
)
async def pid(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None):
    hide = False
    mark = False
    origin = False
    args = text.split(" ")
    if len(args) >= 2:
        text = args[0]
        if "hide" in args or '省略' in args: hide = True
        if "mark" in args or '遮罩' in args: mark = True
        if 'origin' in args or '原图' in args: origin = True
    logger.info(f"text: {text}, hide: {hide}, mark: {mark}, origin: {origin}")

    pid = re.sub(r"((pid|Pid|PID) ?)?", "", text)
    pid = re.sub(
        r"^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=", "", pid
    ).strip()
    pid = re.sub(r"((https?://)?(www.)?pixiv.net/(artworks|i)/)?", "", pid).strip()
    pid = re.sub(r"/?(\?.*)?(#.*)?", "", pid).strip()
    logger.info(f"pid: {pid}")
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

    mid = await update.message.reply_text(
        "请等待...",
        reply_to_message_id=update.message.message_id,
    )
    try:
        r = await util.get(
            f"https://www.pixiv.net/ajax/illust/{pid}",
            proxy=True,
            headers=config.pixiv_headers,
        )
    except Exception:
        return await update.message.reply_text(
            "连接超时",
            reply_to_message_id=update.message.message_id,
        )
    res = r.json()
    if res["error"]:
        return await update.message.reply_text(
            '错误: '+res["message"],
            reply_to_message_id=update.message.message_id,
        )
    msg = parsePidMsg(res["body"], hide)

    imgUrl = res["body"]["urls"]["original"]
    #imgUrl = imgUrl.replace("i.pximg.net", "i.pixiv.re")

    count = res["body"]["pageCount"]
    pcount = (count - 1) // 9 + 1
    bot = context.bot
    
    async def _m():
      nonlocal origin, mid, bot, imgUrl, update, count, pcount
      ms = []
      i = p * 9
      while i < min((p + 1) * 9, count):
          url = imgUrl.replace("_p0", f"_p{i}")
          try:
              img = await util.getImg(url, saveas=f"{pid}_p{i}", ext=True, headers=config.pixiv_headers, proxy=True)
          except Exception:
              await update.message.reply_text(
                  (
                      f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                      if min((p + 1) * 9, count) != 1
                      else ""
                  ) + "图片获取失败",
                  reply_to_message_id=update.message.message_id,
              )
              return False
              
          caption = (
              (msg if i == 0 else "")
              + (
                  f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                  if min((p + 1) * 9, count) > 9
                  else ""
              )
              if len(ms) == 0
              else None
          )
          
          stats = os.stat(img)
          size_M = stats.st_size // 1024 // 1024
          if not origin:
              ms.append(
                  InputMediaPhoto(
                      media=open(img, "rb"),
                      caption=caption,
                      parse_mode="HTML",
                      has_spoiler=mark,
                  )
              )
          else:
              if not origin:
                  i = 0
                  origin = True
                  ms = []
                  continue
              #portion = os.path.splitext(img)
              #new_img = portion[0] + ".png"
              #os.rename(img, new_img)
              ms.append(
                  InputMediaDocument(
                      media=open(img, "rb"),
                      caption=caption,
                      parse_mode="HTML",
                  )
              )
          '''
          else:
              await update.message.reply_text(
                  (
                      f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                      if min((p + 1) * 9, count) != 1
                      else ""
                  )
                  + "图片过大",
                  reply_to_message_id=update.message.message_id,
              )
              return False'''
          i += 1

      try:
          await update.message.reply_media_group(
              media=ms,
              reply_to_message_id=update.message.message_id,
              read_timeout=120,
              write_timeout=120,
              connect_timeout=120,
              pool_timeout=120,
          )
      except Exception:
          logger.info(msg)
          logger.error(traceback.print_exc())
          if not origin:
            origin = True
            return await _m()
          await update.message.reply_text(
              (
                  f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                  if min((p + 1) * 9, count) != 1
                  else ""
              )
              + "发送失败",
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
      return True
    for p in range(pcount):
      await bot.edit_message_text(
          chat_id=update.message.chat_id,
          message_id=mid.message_id,
          text="正在获取 p" +
          f"{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}",
      )
      if not await _m(): return
      
    #await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)
    keyboard = [[]]
    if not origin:
      keyboard[0].append(InlineKeyboardButton("获取原图", callback_data=f"{pid} {'hide' if hide else ''} origin"))
    
    keyboard[0].append(
      InlineKeyboardButton("详细描述" if hide else "简略描述", callback_data=f"{pid} {'hide' if not hide else ''} {'origin' if origin else ''}")
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    mid = await update.message.reply_text(
        "获取完成", 
        reply_to_message_id=update.message.message_id,
        reply_markup=reply_markup,
    )
    #await asyncio.sleep(1)
    #await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)
    #


@inline_handler(r"((^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12})|"
                r"(^((https?://)?(www.)?pixiv.net/(artworks|i)/)?((pid|Pid|PID) ?)?\d{6,12}))" + _end)
async def _(update, context, query):
  text = query

  results = []
  hide = False
  mark = False
  origin = False
  args = text.split(" ")
  if len(args) >= 2:
      text = args[0]
      if "hide" in args or '省略' in args: hide = True
      if "mark" in args or '遮罩' in args: mark = True
      if 'origin' in args or '原图' in args: origin = True
  logger.info(f"text: {text}, hide: {hide}, mark: {mark}, origin: {origin}")

  pid = re.sub(
      r"^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=", "", text
  ).strip()
  pid = re.sub(
      r"((https?://)?(www.)?pixiv.net/(artworks|i)/)?((pid|Pid|PID) ?)?", "", pid
  ).strip()
  pid = re.sub(r"/?(\?.*)?(#.*)?", "", pid).strip()
  if pid == "":
      return

  r = await util.get(
      f"https://www.pixiv.net/ajax/illust/{pid}",
      proxy=True,
      headers=config.pixiv_headers,
  )
  res = r.json()
  if res["error"]:
      return await update.inline_query.answer([])
  msg = parsePidMsg(res["body"], hide)

  imgUrl = res["body"]["urls"]["original"]
  thumbUrl = res["body"]["urls"]["thumb"]
  for i in range(0, res["body"]["pageCount"]):
      url = imgUrl.replace("_p0", f"_p{i}").replace(
          "i.pximg.net", "i.pixiv.re")
      turl = thumbUrl.replace("_p0", f"_p{i}").replace(
          "i.pximg.net", "i.pixiv.re"
      )
      results.append(
          InlineQueryResultPhoto(
              id=str(uuid4()),
              photo_url=url,
              thumbnail_url=turl,
              caption=msg,
              parse_mode="HTML",
          )
      )

  countFlag = len(results) > 1
  btn_text = "获取" + ("遮罩" if mark else "全部") + ("原图" if origin else "图片") + ("(隐藏描述)" if hide else "")
  start_parameter = f"{pid}_{'hide' if hide else ''}_{'mark' if mark else ''}_{'origin' if origin else ''}"
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
  await pid(_update, context, query.data)
  
  
def parsePidMsg(res, hide=False):
    pid = res["illustId"]

    '''tags = []
    for i in res["tags"]["tags"]:
        tags.append("#" + i["tag"])
        if "translation" in i.keys():
            tags.append("#" + i["translation"]["en"])
    tags = (
        json.dumps(tags, ensure_ascii=False)
        .replace('"', "")
        .replace("[", "")
        .replace("]", "")
    )'''

    #types = ["插画", "漫画", "动图（不支持发送，请自行访问p站）"]
    
    props = []
    if res["tags"]["tags"][0]["tag"] == "R-18":
        props.append('#NSFW')
    if res["tags"]["tags"][0]["tag"] == "R-18G":
        props.append('#R18G')
        props.append('#NSFW')
    if res['illustType'] == 2:
      props.append('#动图')
    if res['aiType'] == 2:
        props.append('#AI作品')
    prop = ' '.join(props)
    if prop != '':
        prop += '\n'
    
    #t = dateutil.parser.parse(res["createDate"]) + datetime.timedelta(hours=8)

    '''msg = (
        f"pid: <code>{pid}</code>\n"
        f"作品类型：{types[res['illustType']]}\n"
        f"标题: <b>{res['illustTitle']}</b>\n"
        f"作者: <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>\n"
        f"数量: {res['pageCount']}\n"
        f"{prop}"
        "\n"
        f"{comment}"
        f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">From Pixiv at {t.strftime('%Y年%m月%d日 %H:%M:%S')}</a>"
    )'''
    msg = prop
    msg += f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">{res['illustTitle']}</a> - <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>"
    if not hide:
      comment = res["illustComment"]
      comment = (
          comment.replace("<br />", "\n")
          .replace("<br/>", "\n")
          .replace("<br>", "\n")
          .replace(' target="_blank"', "")
      )
      comment = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', comment)
      if len(comment) > 400:
          comment = re.sub(r'<[^/]+[^<]*(<[^>]*)?$', '', comment[:200])
          comment = re.sub(r'\n$','',comment)
          comment = comment + '\n......'
      if comment != '':
          comment = ':\n' + comment
      msg += comment
    
    return msg
   
   