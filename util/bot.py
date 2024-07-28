import config
from .file import getCache, getWorkFile


async def get_file(file_id, name=None):
  if name is None:
    name = file_id
  file = await config.app.bot.getFile(file_id)
  file_path = file.file_path
  if config.local_mode:
    file_path = file_path.replace(config.base_file_url + config.token + '/', '', 1).replace('/var/lib/', '', 1)
  
  img = getCache(name)
  with open(getWorkFile(file_path), 'rb') as f1:
    with open(img, 'wb') as f2:
      f2.write(f1.read())
  return img
  