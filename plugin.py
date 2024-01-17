import traceback
import re
import os.path
import config
from util.log import logger

class Command:
  def __init__(self, cmd, func, pattern=None, private_pattern=None):
    self.cmd = cmd
    self.func = func
    self.pattern = pattern
    self.private_pattern = private_pattern
  
  def __str__(self):
    res = f'Command(cmd={self.cmd}, func={self.func}'
    if self.pattern is not None:
      res += f', pattern={self.pattern}'
    return res + ')'


class Inline:
  def __init__(self, func, pattern):
    self.func = func
    self.pattern = pattern
    
  def __str__(self):
    return f'Inline(func={self.func})'


def handler(cmd, **kwargs):
    def deco(func):
      config.commands.append(Command(cmd, func, **kwargs))
      
      def wrapper(update, context):
        update.message["text"] = (
          update.message["text"]
          .replace("@"+config.bot.username, "")
          .replace("/"+cmd, "")
          .replace(cmd, "")
          .replace("/start", "")
          .replace("-", " ")
          .strip()
        )
        return func(update, context)
      return wrapper
    return deco
    
    
def inline_handler(pattern):
  def deco(func):
    config.inlines.append(Inline(func, pattern))
    return func
  return deco
    
    
def load_plugin(name):
  try:
    __import__(name, fromlist=[None])
    logger.info('Success to load plugin "' + name + '"')
  except Exception:
    logger.warning('Error to load plugin "' + name + '"')
    logger.warning(traceback.print_exc())
  
  
def load_plugins(dir_name):
  for name in os.listdir(dir_name):
        path = os.path.join(dir_name, name)
        if os.path.isfile(path) and \
                (name.startswith('_') or not name.endswith('.py')):
            continue
        if os.path.isdir(path) and \
                (name.startswith('_') or not os.path.exists(
                    os.path.join(path, '__init__.py'))):
            continue
        m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
        if not m:
            continue
        load_plugin(f'{dir_name}.{m.group(1)}')
        