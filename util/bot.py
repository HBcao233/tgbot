import asyncio
import config
from .file import getCache


async def get_file(file_id, name=None):
  if name is None:
    name = file_id
  file = await config.app.bot.getFile(file_id)
  file_path = file.file_path
  if config.local_mode:
    file_path = file_path.replace(config.base_file_url + config.token + '/', '', 1)
  
  img = getCache(name)
  proc = await asyncio.create_subprocess_exec(
    'docker', 'cp', f'telegram-bot-api:{file_path}', img,
  )
  await proc.wait()
  return img
  