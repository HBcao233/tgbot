import traceback
import re
import os.path
import inspect

import config
from util.log import logger


class Command:
  def __init__(
    self, cmd, func, *,
    pattern=None, 
    private_pattern=None, 
    info="", 
    desc="",
    scope="",
  ):
    self.cmd = cmd
    self.func = func
    self.pattern = pattern
    self.private_pattern = private_pattern
    self.info = info
    self.desc = desc
    self.scope = scope
  
  def __str__(self):
    res = f'Command(cmd={self.cmd}, func={self.func}'
    if self.pattern is not None:
      res += f', pattern={self.pattern}'
    return res + ')'
  

class Inline:
  def __init__(self, func, pattern, *, block=True):
    self.func = func
    self.pattern = pattern
    self.block = block
    
  def __str__(self):
    return f'Inline_Handler(func={self.func})'


class Button:
  def __init__(self, func, pattern):
    self.func = func
    self.pattern = pattern
    
  def __str__(self):
    return f'Button_Handler(func={self.func})'


def handler(cmd, **kwargs):
  def deco(func):
    async def _func(update, context, text=None, *_args, **_kwargs):
      args = inspect.signature(func).parameters
      if 'text' not in args:
        return await func(update, context, *_args, **_kwargs)
      if (
        text is None and 
        getattr(update, 'message', None) and 
        getattr(update.message, 'text', None)
      ):
        text = (
          update.message.text
          .lstrip("/" + cmd)
          .lstrip("@" + config.bot.username)
          .lstrip("/start")
          .lstrip(cmd)
          .strip()
        )
      return await func(update, context, text, *_args, **_kwargs)
    
    config.commands.append(Command(cmd, _func, **kwargs))
    return _func
  return deco
    
    
def inline_handler(pattern, **kwargs):
  def deco(func):
    config.inlines.append(Inline(func, pattern, **kwargs))
    return func
  return deco
    
    
def button_handler(pattern):
  def deco(func):
    config.buttons.append(Button(func, pattern))
    return func
  return deco
  
  
def load_plugin(name):
  try:
    __import__(name, fromlist=[])
    logger.info('Success to load plugin "' + name + '"')
  except Exception:
    logger.warning('Error to load plugin "' + name + '"')
    logger.warning(traceback.print_exc())
  
  
def load_plugins():
  dirpath = os.path.join(config.botRoot, 'plugins')
  for name in os.listdir(dirpath):
    path = os.path.join(dirpath, name)
    if os.path.isfile(path) and \
       (name.startswith('_') or not name.endswith('.py')):
      continue
    if os.path.isdir(path) and \
       (name.startswith('_') or 
        not os.path.exists(os.path.join(path, '__init__.py'))):
      continue
    m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
    if not m:
      continue
    load_plugin(f'{config.botName}.plugins.{m.group(1)}')
        