import re
import traceback
import asyncio
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
)
from telegram.ext import ContextTypes
from bs4 import BeautifulSoup
from urllib.parse import unquote
from uuid import uuid4

import config
import util
from util.log import logger
from plugin import handler


@handler('kid',
  private_pattern=r"((https://)?kemono.(party|su)/)?.+/user/\d+/post/\d+",
  pattern=r"kid ((https://)?kemono.(party|su)/)?.+/user/\d+/post/\d+"
)
async def kid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text: str = update.message["text"]

    if not re.match(r"https://kemono.(party|su)/.+/user/\d+/post/\d+", text):
        return await update.message.reply_text("请输入k站链接")
    kid = text
    mid = await update.message.reply_text(
        "请等待...", reply_to_message_id=update.message.message_id
    )
    r = await util.get(kid, proxy=True, timeout=60)
    msg, files, other = parseKidMsg(kid, r.text)

    count = len(files)
    piece = 10
    pcount = (count - 1) // piece + 1
    bot = update.get_bot()
    for p in range(pcount):
        await bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=mid.message_id,
            text="正在获取 p"
            + f"{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}",
        )
        ms = []
        for i in range(p * piece, min((p + 1) * piece, count)):
            file = files[i]
            a = {
                "attachment": InputMediaDocument,
                "image": InputMediaPhoto,
                "video": InputMediaVideo,
            }
            try:
                img = await util.getImg(file["url"], proxy=True)
            except Exception:
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
            ms.append(
                a[file["type"]](
                    media=open(img, "rb"),
                    caption=caption,
                    parse_mode="HTML",
                )
            )

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
    mid = await update.message.reply_text(
        "获取完成", reply_to_message_id=update.message.message_id
    )
    await asyncio.sleep(3)
    await bot.delete_message(chat_id=update.message.chat_id, message_id=mid.message_id)


def parseKidMsg(kid, _html):
    soup = BeautifulSoup(_html, "html.parser")
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

    # published_time = soup.select(
    #     ".site-section--post .post__header .post__info .post__published .timestamp"
    # )[0].text.strip()

    msg = f'<a href="{kid}">{title}</a> - <a href="{user_url}">{user_name}</a>:'
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
    msg_add(f"\n\n{kid}")

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
