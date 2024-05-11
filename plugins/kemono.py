import re
import os.path
import traceback
import asyncio
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
from urllib.parse import unquote
from uuid import uuid4
import httpx

import config
import util
from util.log import logger
from plugin import handler, button_handler


private_pattern = r"((https://)?kemono.(party|su)/)?[^/]+(/user/\d+)?(/post)?/\d+"
@handler('kid',
  private_pattern="^"+private_pattern,
  pattern="^kid " + private_pattern,
  info="kenomo爬取 /kid <url> [hide] [mark]"
)
async def kid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    text: str = update.message["text"] if text is None else text

    hide = False
    mark = False
    origin = False
    args = text.split(" ")
    if len(args) >= 2:
        text = args[0]
        if "hide" in args or '省略' in args: hide = True
        if "mark" in args or '遮罩' in args: mark = True
        if 'origin' in args or '原图' in args: origin = True
    logger.info(f"text: {text}, hide: {hide}, mark: {mark}")

    if not re.match(private_pattern, text):
        return await update.message.reply_text(
          "用法: /kid <url> [hide] [mark/遮罩] [origin/原图]"
        )
    bot = context.bot
    _kid = re.sub(r'((https://)?kemono.(party|su)/)?([^/]+)(/user/\d+)?(/post)?/(\d+)', r'\4/\7', text)
    #logger.info(_kid)
    arr = _kid.split('/')
    kid = 'https://kemono.su/' + arr[0] + '/post/' + arr[1]
    mid = await update.message.reply_text(
        "请等待...", reply_to_message_id=update.message.message_id
    )
    r = await util.get(kid)
    try:
      msg, files, other = parseKidMsg(kid, r.text, hide)
    except Exception as e:
      return await bot.edit_message_text(
          chat_id=update.message.chat_id,
          message_id=mid.message_id,
          text=e,
      )
      
    if 'fanbox' in _kid and len(files) > 1:
      files = files[1:]
      
    count = len(files)
    piece = 10
    pcount = (count - 1) // piece + 1
    for p in range(pcount):
        await bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=mid.message_id,
            text="正在获取 p"
            + f"{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}",
        )
        ms = []
        i = p * piece
        while i < min((p + 1) * piece, count):
            file = files[i]
            url = file["url"] if origin else file['thumbnail']
            try:
              img = await util.getImg(
                url, 
                timeout=httpx.Timeout(
                  timeout=60, connect=60, 
                  read=60, write=60
                ),
              )
            except Exception:
              logger.error(traceback.print_exc())
              return await update.message.reply_text("文件获取失败")
                
            caption = ''
            if p == 0 and len(ms) == 0:
                caption += msg
            if len(ms) == 0:
                caption += (
                    f"\n{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}"
                    if min((p + 1) * piece, count) != 1
                    else ""
                )
                
            #stats = os.stat(img)
            #size_M = stats.st_size // 1024 // 1024
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
                portion = os.path.splitext(img)
                new_img = portion[0] + ".png"
                os.rename(img, new_img)
                ms.append(
                    InputMediaDocument(
                        media=open(new_img, "rb"),
                        caption=caption,
                        parse_mode="HTML",
                    )
                )
            i += 1

        try:
            resm = await update.message.reply_media_group(
                media=ms,
                reply_to_message_id=update.message.message_id,
                read_timeout=180,
                write_timeout=180,
                connect_timeout=180,
                pool_timeout=180,
            )
            resmid = resm[0]
        except Exception:
            logger.error(traceback.print_exc())
            logger.info(msg)
            await update.message.reply_text("发送失败")
            return await bot.delete_message(
                chat_id=update.message.chat_id, message_id=mid.message_id
            )

        await bot.delete_message(
            chat_id=update.message.chat_id, message_id=mid.message_id
        )
        mid = await update.message.reply_text(
            "请等待...", reply_to_message_id=update.message.message_id
        )

    for i in other:
        resmid = await update.message.reply_text(
            i,
            reply_to_message_id=resmid.message_id,
            parse_mode="HTML",
        )
    await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)
    keyboard = [
        [
            InlineKeyboardButton("获取原图", callback_data=f"{_kid} {'hide' if hide else ''} origin"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    mid = await update.message.reply_text(
        "获取完成", 
        reply_to_message_id=update.message.message_id,
        reply_markup=reply_markup if not origin else None,
    )
    #await asyncio.sleep(3)
    #await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)


@button_handler(pattern=r"[^/]+/\d+")
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


def parseKidMsg(kid, _html, hide=False):
    soup = BeautifulSoup(_html, "html.parser")
    try:
      user_name = soup.select(".site-section--post .post__header .post__user-name")[
          0
      ].text.strip()
  
      user_u: str = soup.select(".site-section--post .post__header .post__user-name")[
          0
      ].attrs["href"]
      user_uid = user_u.split("/")[-1]
      user_url = f"https://www.pixiv.net/fanbox/creator/{user_uid}"
  
      title = soup.select(
          ".site-section--post .post__header .post__info .post__title span"
      )[0].text.strip()
    except Exception:
      raise Exception('解析错误')
    # published_time = soup.select(
    #     ".site-section--post .post__header .post__info .post__published .timestamp"
    # )[0].text.strip()

    msg = f'<a href="{kid}">{title}</a> - <a href="{user_url}">{user_name}</a>'
    if not hide: msg += ':'
    msg1 = ""
    other = []

    def msg1_add(add):
        nonlocal msg1, other
        if len(msg1 + add) > 1024:
            other.append(msg1)
            msg1 = ""
        msg1 += add

    def msg_add(add, length=950):
        nonlocal msg, msg1, other
        if len(msg + add) > length:
            msg1_add(add)
        else:
            msg += add
            
    if not hide:
      post__content = soup.select(
          ".site-section--post .post__body .post__content")
      if len(post__content) > 0:
          contents = post__content[0].children
          for i in contents:
              ii = i.text.strip()
              if ii != "":
                  if i.name == "h2":
                      add = f"\n<b>{ii}</b>"
                  else:
                      add = f"\n{ii}"
                  if len(msg + add) < 400:
                      msg_add(add)
                  else:
                      msg_add('\n……')
                      break

    # msg_add(f'\n\n<a href="{kid}">{published_time}</a>')
    # msg_add(f"\n\n{kid}")

    _attachments = soup.select(
        ".site-section--post .post__body .post__attachments li")
    if len(_attachments) > 0:
        msg_add("\n\n文件列表: ")
    for i in _attachments:
        add = f"\n<code>{unquote(i.select('a')[0].attrs['download'])}</code>: {i.select('a')[0].attrs['href']}"
        msg_add(add)

    # _summarys = soup.select(".post__body ul li summary")
    # if len(_summarys) > 0:
    #     msg1_add("\n\n视频列表: ")
    # for i in _summarys:
    #     msg1_add(
    #         f"\n<code>{i.text.strip()}</code>: {i.parent.select('video source')[0].attrs['src']}"
    #     )
    if msg1 != "":
        other.append(msg1)

    files = []
    _files = soup.select(
        ".site-section--post .post__body .post__files .post__thumbnail a"
    )
    for i, ai in enumerate(_files):
        url = ai.attrs["href"]
        ext = url.split(".")[-1]
        if len(ai.select("img")) > 0:
            files.append(
                {
                    "name": f"{i}.{ext}",
                    "type": "image",
                    "url": url,
                    "thumbnail": "https:" + ai.select("img")[0].attrs["src"],
                }
            )

    return msg, files, other
