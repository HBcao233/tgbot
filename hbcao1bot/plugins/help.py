import re
import traceback
from telegram import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  InputMediaPhoto,
  InputMediaVideo,
)
from plugin import handler
from util import logger


@handler('help', info='介绍与帮助')
async def help(update, context, text=''):
  keyboard = [[
    InlineKeyboardButton("源代码", url=f"https://github.com/HBcao233/tgbot"),
  ]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  return await update.message.reply_text(
    "Hi! 这里是小派魔! \n"
    "指令列表: \n"
    "/pid <url/pid>: 获取p站作品 (类似 @Pixiv_bot\n"
    "/tid <url/tid>: 获取推文 (类似 @TwPicBot\n"
    "/bill <url/aid/bvid>: 获取b站视频 (类似 @bilifeedbot\n"
    "/eid <url>: e站爬取\n"
    "/kid <url>: kemono爬取\n"
    "小提示: 私聊可直接发送url/pid/tid: 自动识别可进行的爬取\n"
    "/roll [min=0][ -~/][max=9]: 返回一个min~max的随机数（默认0-9）\n",
    reply_markup=reply_markup,
  )
    
    
_file_pattern = r"(vi_|p_|d_|au_)([a-zA-Z0-9-_]+)"
@handler(
  "file", 
  #private_pattern=_file_pattern
)
async def file(update, context, text):
  bot = context.bot
  r = re.findall(_file_pattern, text)
  # logger.info(r)

  ms = []
  async def _s():
    nonlocal ms, bot
    if len(ms) > 0:
      await bot.sendMediaGroup(chat_id=update.message.chat_id, media=ms, reply_to_message_id=update.message.message_id)
      ms = []
  
  for i in r:
    try:
      if i[0] == 'p_':
        ms.append(InputMediaPhoto(media=i[1]))
      elif i[0] == 'vi_':
        ms.append(InputMediaVideo(media=i[1]))
      elif i[0] == 'd_':
        await _s()
        await bot.sendDocument(chat_id=update.message.chat_id, document=i[1], reply_to_message_id=update.message.message_id)
      elif i[0] == 'au_':
        await _s()
        await bot.sendAudio(chat_id=update.message.chat_id, audio=i[1], reply_to_message_id=update.message.message_id)
    except Exception:
      logger.error(traceback.print_exc())
      await bot.sendMessage(chat_id=update.message.chat.id, text="Error, maybe non-existent", reply_to_message_id=update.message.message_id)
  await _s()
  