import re
import traceback
import asyncio
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaDocument,
    LinkPreviewOptions,
)
from telegram.ext import ContextTypes
from uuid import uuid4
from bs4 import BeautifulSoup
import ujson as json

import config
import util
from util.log import logger
from plugin import handler
from .data_source import parseEidSMsg, parseEidGMsg, parsePage


@handler('eid',
  private_pattern=r"https?://e[x-]hentai.org/[sg]/.*",
  pattern=r"eid https?://e[x-]hentai.org/[sg]/.*",
  info="e站爬取 /eid <url> [hide] [mark]"
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
    r = await util.get(text, params={'p': 0}, headers=config.ex_headers)
    html0 = r.text
    if "Your IP address has been" in html0:
        return await update.message.reply_text("IP被禁")
    if "Not Found" in html0:
        return await update.message.reply_text("页面不存在")
    
    soup = BeautifulSoup(html0, "html.parser")
    title, num, magnets = await parseEidGMsg(text, soup)
    
    with util.Data('urls') as data:
      if not (url := data[text]):
        url = await parsePage(text, soup, title)
        if not url:
          return await context.bot.edit_message_text(
            chat_id=update.message.chat_id, 
            message_id=mid.message_id,
            text='获取失败',
          )
        data[text] = url
    
    msg = (
      f'标题: <code>{title}</code>\n'
      f'预览: <a href="{url}">{url}</a>\n'
      f"数量: {num}\n" 
      f"原链接: {text}"
    )
    
    if len(magnets) > 0:
      msg += "\n磁力链："
    for i in magnets:
      msg += f"\n· <code>{i}</code>"
    
    await update.message.reply_text(
      text=msg,
      reply_to_message_id=update.message.message_id,
      parse_mode="HTML",
      link_preview_options=LinkPreviewOptions(
        url=url,
        prefer_large_media=True,
        show_above_text=False,
      ),
    )
    
    await context.bot.delete_message(
      chat_id=update.message.chat_id, message_id=mid.message_id
    )
