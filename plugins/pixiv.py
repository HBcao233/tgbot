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
from plugin import handler, inline_handler
    

@handler('pid', 
  private_pattern=r"(^https://(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12}(#.*)?( ?hide ?)?( ?mark ?)?$)|"
                  r"^(https://(www.)?pixiv.net/(artworks|i)/)?\d{6,12}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$",
  pattern=r"(^((pid|Pid|PID) ?)https://(www.)?pixiv.net/member_illust.php?.*illust_id=\d{6,12}(#.*)?( ?hide ?)?( ?mark ?)?$)|"
        r"^((pid|Pid|PID) ?)(https://(www.)?pixiv.net/(artworks|i)/)?\d{6,12}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$",
)
async def pid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message["text"]

    hide = False
    mark = False
    args = text.split(" ")
    if len(args) >= 2:
        text = args[0]
        if "hide" in args:
            hide = True
        if "mark" in args:
            mark = True
    logger.info(f"text: {text}, hide: {hide}, mark: {mark}")

    pid = re.sub(r"((pid|Pid|PID) ?)?", "", text)
    pid = re.sub(
        r"^https://(www.)?pixiv.net/member_illust.php?.*illust_id=", "", pid
    ).strip()
    pid = re.sub(r"(https://(www.)?pixiv.net/(artworks|i)/)?", "", pid).strip()
    pid = re.sub(r"(_.*)(\?.*)?(#.*)?", "", pid).strip()
    logger.info(f"pid: {pid}")
    if pid == "":
        return await update.message.reply_text(
            "用法: /pid <url/pid>\n"
            "url/pid: p站链接或pid\n"
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
        
    if hide:
        msg = f"https://www.pixiv.net/artworks/{pid}"
    else:
        msg = parsePidMsg(res["body"])

    imgUrl = res["body"]["urls"]["original"]
    #imgUrl = imgUrl.replace("i.pximg.net", "i.pixiv.re")

    count = res["body"]["pageCount"]
    pcount = (count - 1) // 9 + 1
    bot = update.get_bot()
    for p in range(pcount):
        await bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=mid.message_id,
            text="正在获取 p" +
            f"{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}",
        )
        ms = []
        flag = False
        i = p * 9
        while i < min((p + 1) * 9, count):
            url = imgUrl.replace("_p0", f"_p{i}")
            try:
                img = await util.getImg(url, headers=config.pixiv_headers, proxy=True)
            except Exception:
                return await update.message.reply_text(
                    (
                        f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                        if min((p + 1) * 9, count) != 1
                        else ""
                    ) + "图片获取失败",
                    reply_to_message_id=update.message.message_id,
                )
                
            caption = (
                (msg if i == 0 else "")
                + (
                    f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                    if min((p + 1) * 9, count) != 1
                    else ""
                )
                if len(ms) == 0
                else None
            )
            stats = os.stat(img)
            size_M = stats.st_size // 1024 // 1024
            if size_M < 5 and not flag:
                ms.append(
                    InputMediaPhoto(
                        media=open(img, "rb"),
                        caption=caption,
                        parse_mode="HTML",
                        has_spoiler=mark,
                    )
                )
            elif size_M < 20:
                if not flag:
                    i = 0
                    flag = True
                    ms = []
                    continue
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
            else:
                return await update.message.reply_text(
                    (
                        f"\n{p * 9 + 1} ~ {min((p + 1) * 9, count)} / {count}"
                        if min((p + 1) * 9, count) != 1
                        else ""
                    )
                    + "图片过大",
                    reply_to_message_id=update.message.message_id,
                )
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
        mid = await update.message.reply_text(
            "请等待...",
            reply_to_message_id=update.message.message_id,
        )

    await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)
    mid = await update.message.reply_text(
        "获取完成", 
        reply_to_message_id=update.message.message_id
    )
    await asyncio.sleep(1)
    await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)
    #keyboard = [
    #    [
    #        InlineKeyboardButton("⭕ 发送", callback_data="done"),
    #        InlineKeyboardButton("❌ 取消", callback_data="cancel"),
    #    ],
    #]
    #reply_markup = InlineKeyboardMarkup(keyboard)


@inline_handler(r"^(https://(www.)?pixiv.net/(artworks|i)/)?((pid|Pid|PID) ?)?\d{6,12}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$")
async def _(update, context, query):
  text = query.replace("/pid", "")

  results = []
  hide = False
  mark = False

  args = text.split(" ")
  if len(args) >= 2:
      text = args[0]
      if "hide" in args:
          hide = True
      if "mark" in args:
          mark = True
  logger.info(f"text: {text}, hide: {hide}, mark: {mark}")

  pid = re.sub(
      r"(https://(www.)?pixiv.net/(artworks|i)/)?((pid|Pid|PID) ?)?", "", text
  ).strip()
  pid = re.sub(r"(\?.*)?(#.*)?", "", pid).strip()
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
  if not hide:
      msg = parsePidMsg(res["body"])
  else:
      msg = f"https://www.pixiv.net/artworks/{pid}"
  logger.info(msg)

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
  await update.inline_query.answer(
      results,
      cache_time=10,
      button=InlineQueryResultsButton(
          text="获取全部图片" + ("(隐藏信息)" if hide else ""),
          start_parameter=query.replace(" ", "-"),
      )
      if countFlag or mark
      else None,
      read_timeout=60,
      write_timeout=60,
      connect_timeout=60,
      pool_timeout=60,
  )
  
  
def parsePidMsg(res):
    pid = res["illustId"]

    # tags = []
    # for i in res["tags"]["tags"]:
    #     tags.append("#" + i["tag"])
    #     if "translation" in i.keys():
    #         tags.append("#" + i["translation"]["en"])
    # tags = (
    #     json.dumps(tags, ensure_ascii=False)
    #     .replace('"', "")
    #     .replace("[", "")
    #     .replace("]", "")
    # )

    types = ["插画", "漫画", "动图（不支持发送，请自行访问p站）"]
    
    props = []
    if res["tags"]["tags"][0]["tag"] == "R-18":
        props.append('#NSFW')
    if res['aiType'] == 2:
        props.append('#AI作品')
    prop = ' '.join(props)
    if prop != '':
        prop += '\n'
    
    t = dateutil.parser.parse(res["createDate"]) + datetime.timedelta(hours=8)

    comment = res["illustComment"]
    comment = (
        comment.replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
        .replace(' target="_blank"', "")
    )
    if len(comment) > 200:
        comment = re.sub('<[^/]+[^<]*(<[^>]*)?$', '', comment[:200])
        comment = re.sub('\n$','',comment)
        comment = comment + '\n......'
    if comment != '':
        comment += '\n\n'
    msg = (
        f"pid: <code>{pid}</code>\n"
        f"作品类型：{types[res['illustType']]}\n"
        f"标题: <b>{res['illustTitle']}</b>\n"
        f"作者: <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>\n"
        f"数量: {res['pageCount']}\n"
        f"{prop}"
        "\n"
        f"{comment}"
        f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">From Pixiv at {t.strftime('%Y年%m月%d日 %H:%M:%S')}</a>"
    )
    return msg
    