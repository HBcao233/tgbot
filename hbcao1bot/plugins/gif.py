import asyncio

import config
import util
from util import logger
from plugin import handler


@handler('gif', info="视频转gif")
async def _gif(update, context, text=None):
  message = update.message
  bot = context.bot
  if not getattr(message, 'reply_to_message', None):
    return await message.reply_text(
      '请用命令回复一条消息',
      reply_to_message_id=message.message_id,
    )
  reply_msg = message.reply_to_message
  if getattr(reply_msg, 'sticker', None):
    file_id = reply_msg.sticker.file_id
    file_unique_id = reply_msg.sticker.file_unique_id
  elif getattr(reply_msg, 'document', None):
    file_id = reply_msg.document.file_id
    file_unique_id = reply_msg.document.file_unique_id
  elif getattr(reply_msg, 'video', None):
    file_id = reply_msg.document.file_id
    file_unique_id = reply_msg.document.file_unique_id
  else:
    return await message.reply_text(
      '回复的消息不是一个视频',
      reply_to_message_id=message.message_id,
    )
  
  data = util.Documents()
  if not (document := data[file_unique_id]):
    img = await util.bot.get_file(file_id)
    
    palette = util.getCache(file_unique_id + '_palette.png')
    command = [
      'ffmpeg', 
      '-i', img, 
      '-vf', 'palettegen', 
      palette, '-y'
    ]
    proc = await asyncio.create_subprocess_exec(
      *command,
      stdout=asyncio.subprocess.PIPE, 
      stdin=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0 and stderr: 
      logger.warning(stderr.decode('utf8'))
      return False
  
    output = util.getCache(file_unique_id + '_gif.gif')
    command = [
      'ffmpeg', 
      '-i', img,
      '-i', palette,
      '-filter_complex', 'paletteuse',
      output, '-y'
    ]
    proc = await asyncio.create_subprocess_exec(
      *command,
      stdout=asyncio.subprocess.PIPE, 
      stdin=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0 and stderr: 
      logger.warning(stderr.decode('utf8'))
      return False
      
    document = open(output, 'rb')
  m = await message.reply_document(
    document=document,
    reply_to_message_id=message.message_id,
    disable_content_type_detection=True,
    # filename=file_unique_id + '.gif'
  )
  data[file_unique_id] = m.document.file_id
  