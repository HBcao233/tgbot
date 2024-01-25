import re
import traceback
import asyncio
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaDocument,
)
from telegram.ext import ContextTypes
from uuid import uuid4
from bs4 import BeautifulSoup

import config
import util
from util.log import logger
from plugin import handler


@handler('eid',
  private_pattern=r"https?://e[x-]hentai.org/[sg]/.*",
  pattern=r"eid https?://e[x-]hentai.org/[sg]/.*"
)
async def eid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    text: str = update.message["text"] if text is None else text

    mark = False
    args = text.split(" ")
    if len(args) >= 2:
        text = args[0]
        if "mark" in args:
            mark = True
    logger.info(f"text: {text}, mark: {mark}")

    match = re.match(r"https?://e[x-]hentai.org/[sg]/.*", text)
    if not match:
        return await update.message.reply_text("请输入e站 url")

    # 单页图片
    if "hentai.org/s/" in text:
        r = await util.get(text, headers=config.ex_headers, proxy=True)
        html = r.text
        if "Your IP address has been" in html:
            return await update.message.reply_text("梯子IP被禁，请联系管理员更换梯子")
        if "Not Found" in html:
            return await update.message.reply_text("页面不存在")

        msg, url = parseEidSMsg(text, html)
        try:
            img = await util.getImg(url, proxy=True, headers=config.ex_headers)
            await update.message.reply_photo(
                open(img, "rb"),
                caption=msg,
                reply_to_message_id=update.message.message_id,
                has_spoiler=mark,
            )
        except Exception:
            logger.warning(traceback.format_exc())
            return update.message.reply_text("媒体发送失败")

    # 画廊
    if "hentai.org/g/" in text:
        mid = await update.message.reply_text(
            "请等待...", reply_to_message_id=update.message.message_id
        )
        r = await util.get(text, headers=config.ex_headers, proxy=True)
        html = r.text
        if "Your IP address has been" in html:
            return await update.message.reply_text("梯子IP被禁，请联系管理员更换梯子")
        if "Not Found" in html:
            return await update.message.reply_text("页面不存在")

        msg, num, urls = await parseEidGMsg(text, html)
        imgs = []
        r = await util.get(urls[0], headers=config.ex_headers, proxy=True)
        html1 = r.text
        soup1 = BeautifulSoup(html1, "html.parser")
        imgs.append(soup1.select("#i3 img")[0].attrs["src"])
        img = await util.getImg(imgs[0], proxy=True, headers=config.ex_headers)
        await update.message.reply_photo(
            photo=open(img, "rb"),
            caption=msg,
            reply_to_message_id=update.message.message_id,
            parse_mode="HTML",
        )
        
        bot = update.get_bot()
        await bot.delete_message(
            chat_id=update.message.chat_id, message_id=mid.message_id
        )
        mid = await update.message.reply_text(
            "请等待...", reply_to_message_id=update.message.message_id
        )

        count = len(urls)
        piece = 10
        pcount = (count - 1) // piece + 1
        for p in range(pcount):
            p_tip = f"{p * piece + 1} ~ {min((p + 1) * piece, count)} / {count}"
            caption = p_tip if min((p + 1) * piece, count) != 1 else ""
            pp_tip = ("(由于性能小派魔最多获取40张)" if count == 40 and num > 40 else "")

            await bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=mid.message_id,
                text="正在获取 p" + p_tip + (pp_tip if p == 0 else ""),
            )
            ms = []
            for i in range(p * piece, min((p + 1) * piece, count)):
                r = await util.get(urls[i], headers=config.ex_headers, proxy=True)
                html1 = r.text
                soup1 = BeautifulSoup(html1, "html.parser")
                url = soup1.select("#i3 img")[0].attrs["src"]
                img = await util.getImg(url, proxy=True, headers=config.ex_headers)
                ms.append(
                    InputMediaPhoto(
                        media=open(img, "rb"),
                        caption=caption if len(ms) == 0 else None,
                        parse_mode="HTML",
                    )
                )

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
                await update.message.reply_text(p_tip + " 发送失败")

            await bot.delete_message(
                chat_id=update.message.chat_id, message_id=mid.message_id
            )
            mid = await update.message.reply_text(
                "请等待...", reply_to_message_id=update.message.message_id
            )

        await bot.delete_message(
            chat_id=update.message.chat_id, message_id=mid.message_id
        )
        mid = await update.message.reply_text(
            "获取完成", reply_to_message_id=update.message.message_id
        )
        await asyncio.sleep(1)
        await bot.delete_message(
            chat_id=update.message.chat_id, message_id=mid.message_id
        )


def parseEidSMsg(eid, _html):
    '''
    格式化e站s单页 msg
    '''
    soup = BeautifulSoup(_html, "html.parser")
    name = soup.select("#i1 h1")[0].string
    url = soup.select("#i3 img")[0].attrs["src"]
    sn = soup.select("#i2 .sn div")[0].text

    prev = soup.select("#i2 #prev")[0].attrs["href"]
    next = soup.select("#i2 #next")[0].attrs["href"]
    source = soup.select("#i7 a")[0].attrs["href"]
    parent = soup.select("#i5 a")[0].attrs["href"]
    return (
        f"\n<code>{name}</code>\n"
        f"{sn}\n"
        f"前：{prev}\n"
        f"后：{next}\n"
        f"原图：{source}\n"
        f"画廊：{parent}"
        f"\n\n{eid}",
        url
    )


async def parseEidGMsg(eid, _html):
    '''
    格式化e站g画廊 msg
    '''
    soup = BeautifulSoup(_html, "html.parser")
    name1 = soup.select("#gd2 #gn")[0].string
    name2 = soup.select("#gd2 #gj")[0].string
    num = soup.select("#gdd tr")[5].select(".gdt2")[
        0].text.replace(" pages", "")

    first = soup.select("#gdt a")[0].attrs["href"]
    r = await util.get(first, headers=config.ex_headers, proxy=True)
    html1 = r.text
    soup1 = BeautifulSoup(html1, "html.parser")
    # first_url = soup1.select("#i3 img")[0].attrs["src"]
    # img = await getImg(first_url, proxy=True, headers=config.ex_headers)

    msg = f"\n<code>{name1}</code>" + f"\n<code>{name2}</code>" + f"\n数量: {num}"

    url = soup.select("#gd5 p")[2].a.attrs["onclick"].split("'")[1]
    r = await util.get(url, headers=config.ex_headers, proxy=True)
    html = r.text
    soup2 = BeautifulSoup(html, "html.parser")

    magnets = []
    for i in soup2.select("table a"):
        torrent = i.attrs["href"]
        if torrent:
            match = re.search(r"(?<=/)([0-9a-f]{40})(?=.torrent)", torrent)
            if match:
                magnet = "magnet:?xt=urn:btih:" + str(match.group())
                magnets.append(magnet)

    if len(magnets) > 0:
        msg += "\n磁力链："
    for i in magnets:
        msg += f"\n<code>{i}</code>"
    msg += f"\n\n{eid}"
    urls = []
    for i in soup.select("#gdt a"):
        urls.append(i.attrs["href"])
    return msg, int(num), urls