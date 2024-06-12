import re
import random
from telegram import (
  InlineQueryResultArticle,
  InputTextMessageContent,
)

from uuid import uuid4

import config
import util
from util.log import logger
from plugin import handler, inline_handler


@handler(
  'roll', 
  info="生成随机数 /roll [min=0] [max=9]",
  private_pattern=r"^roll ?(?:([-\d]+([ \/\~\-]+[-\d]+)?)|[ \/\~\-]+[-\d]+)?$",
)
async def roll(update, context, text, _min=None, _max=None):
    f = 0
    if _min is None or _max is None:
      _min, _max = getMinMax(text)
      f = 1
    res = random.randint(_min, _max)
    msg = f'🎲 骰到了 {res} (在 {_min} ~ {_max} 中)' 
    if f:
      return await update.message.reply_text(msg)
    else: 
      return msg
    
    
@inline_handler(r"^(?:roll ?)?(?:([-\d]+([ \/\~\-]+[-\d]+)?)|[ \/\~\-]+[-\d]+)?$", block=False)
async def _(update, context, text):
  _min, _max = getMinMax(text)
  r = random.randint(_min, _max)
  msg = f'🎲 骰到了 {r} (在 {_min} ~ {_max} 中)'
  res = InlineQueryResultArticle(
      id=str(uuid4()),
      title="🎲 随机数",
      description=f"🎲 生成随机数 (在 {_min} ~ {_max} 中)",
      input_message_content=InputTextMessageContent(
          msg
      ),
      thumbnail_url=r"https://i.postimg.cc/VsR2Dp6K/image.png"
  )
  return [res], None
  
  
def getMinMax(text):
  text = text.replace('roll', '').strip()
  text = re.sub(r'(\d+)- ?(\d+)', r'\1 \2', text)
  f = False
  _min = 1
  _max = 10
  arr = re.split(r'([ \/~])', text)
  logger.info(arr)
  for i in arr:
    if re.match(r'^-?[\d]+$', i):
      if f: 
        _min = int(i)
      else:
        _max = int(i)
    elif re.match(r'[ \/~]', i):
      f = True
  if _min > _max: 
    _min, _max = _max, _min
  return _min, _max