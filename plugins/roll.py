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
  private_pattern=r"^roll( ?[-\d]+( |/|~|-)+[-\d]+)?$",
)
async def roll(update, context, text, _min=None, _max=None):
    if _min is None or _max is None:
      _min, _max = getMinMax(text)
    res = random.randint(_min, _max)
    msg = f'🎲 骰到了 {res} (在 {_min} ~ {_max} 中)' 
    if _min is None or _max is None:
      return await update.message.reply_text(msg)
    else: 
      return msg
    
    
@inline_handler(r"^$|(^(roll ?)?[-\d]+( |/|~|-)+[-\d]+$)", block=False)
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
  text = re.sub(r'(\d+)-(\d+)', r'\1 \2', text)
  arr = list(filter(lambda x: x != '', re.split(r' |/|~', text)))
  try:
    _min = int(arr[0])
  except Exception:
    _min = 0
  try:
    _max = int(arr[1])
  except Exception:
    _max = 9
  return _min, _max