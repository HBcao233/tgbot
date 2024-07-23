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
      quote=True,
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
      quote=True,
    )
    
  mid = await message.reply_text('转换中', quote=True)
  
  data = util.Documents()
  if not (document := data[file_unique_id]):
    img = await util.bot.get_file(file_id, file_unique_id)
    
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
  
    output = util.getCache(file_unique_id + '.gif')
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
    quote=True,
    disable_content_type_detection=True,
  )
  await bot.delete_message(chat_id=mid.chat.id, message_id=mid.message_id)
  data[file_unique_id] = m.document.file_id
  data.save()
  
  
@handler('mp4', info="动图转mp4")
async def _mp4(update, context, text=None):
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
      '回复的消息不是一个动图/视频',
      reply_to_message_id=message.message_id,
    )
  
  mid = await message.reply_text('转换中', quote=True)
    
  data = util.Videos()
  if not (info := data[file_unique_id]):
    img = await util.bot.get_file(file_id, file_unique_id)
  
    output = util.getCache(file_unique_id + '.mp4')
    command = [
      'ffmpeg', 
      '-i', img,
      '-pix_fmt', 'yuv420p',
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
      
    info = util.videoInfo(output)
  video, duration, width, height, thumbnail = tuple(info)
  
  m = await message.reply_video(
    video=video,
    duration=int(duration),
    width=int(width),
    height=int(height),
    thumbnail=thumbnail,
    supports_streaming=True,
    quote=True,
    read_timeout=60,
    write_timeout=60,
    connect_timeout=60,
    pool_timeout=60,
  )
  await bot.delete_message(chat_id=mid.chat.id, message_id=mid.message_id)
  v = m.video
  data[file_unique_id] = [v.file_id, v.duration, v.width, v.height, v.thumbnail.file_id]
  data.save()
  