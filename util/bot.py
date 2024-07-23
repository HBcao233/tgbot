import asyncio
import config


async def get_file(file_id):
  file = await config.app.bot.getFile(file_id)
  file_path = file.file_path
  if config.local_mode:
    file_path = file_path.replace(config.base_file_url + config.token + '/', '', 1)
  
  img = util.getCache(file_unique_id)
  proc = await asyncio.create_subprocess_exec(
    'docker', 'cp', f'telegram-bot-api-telegram-bot-api-1:{file_path}', img,
  )
  await proc.wait()
  return img
  