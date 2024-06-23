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
from datetime import datetime

import util
from util.log import logger
from plugin import handler
from .data_source import headers, parseEidSMsg, parseEidGMsg, parsePage
from util.progress import Progress


_pattern = r'(?:https?://)?(e[x-])hentai\.org/([sg])/([0-9a-z]+)/([0-9a-z-]+)'
@handler('eid',
  private_pattern='^'+_pattern,
  pattern=r"eid "+_pattern,
  info="e站爬取 /eid <url> [hide] [mark]"
)
async def eid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
  text: str = update.message["text"] if text is None else text

  mark = False
  nocache = False
  args = text.split(" ")
  if len(args) >= 2:
    text = args[0]
    if "mark" in args:
      mark = True
    if 'nocache' in args:
      nocache = True
  logger.info(f"text: {text}, mark: {mark}")

  if not (match := re.match(_pattern, text)):
    return await update.message.reply_text("请输入e站 url")
  
  arr = [match.group(i) for i in range(1, 5)]
  # 单页图片
  if arr[1] == "s":
    r = await util.get(text, headers=headers)
    html = r.text
    if "Your IP address has been" in html:
        return await update.message.reply_text("梯子IP被禁，请联系管理员更换梯子")
    if "Not Found" in html:
        return await update.message.reply_text("页面不存在")

    msg, url = parseEidSMsg(text, html)
    try:
        img = await util.getImg(url, proxy=True, headers=headers)
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
  if arr[1] == "g":
    mid = await update.message.reply_text(
        "请等待...", reply_to_message_id=update.message.message_id
    )
    r = await util.get(text, params={'p': 0}, headers=headers)
    html0 = r.text
    if "Your IP address has been" in html0:
        return await update.message.reply_text("IP被禁")
    if "Not Found" in html0:
        return await update.message.reply_text("页面不存在")
    
    soup = BeautifulSoup(html0, "html.parser")
    title, num, magnets = await parseEidGMsg(text, soup)
    logger.info(title)
    if not title:
      return await context.bot.edit_message_text(
        chat_id=update.message.chat_id, 
        message_id=mid.message_id,
        text='获取失败',
      )
    
    now = datetime.now()
    key = '/'.join(arr) + f'.{now:%Y.%m.%d}'
    logger.info(key)
    with util.Data('urls') as data:
      if not (url := data[key]) or nocache:
        bar = Progress(context.bot, mid)
        url = await parsePage(text, soup, title, num, nocache, bar)
        if not url:
          return await context.bot.edit_message_text(
            chat_id=update.message.chat_id, 
            message_id=mid.message_id,
            text='获取失败',
          )
        data[key] = url
    
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
