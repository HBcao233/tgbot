import os.path
import config


def getFile(dir_name='', name=''):
  name = str(name)
  path = os.path.join(config.botRoot, dir_name)
  if '/' in name:
    p, name = os.path.split(name)
    path = os.path.join(path, p)
  if name == '':
    return path
    
  f = ''
  for i in os.listdir(path):
    if os.path.splitext(i)[0] == name:
      f = i
      break
  if f == "":
    f = name
    if "." not in f:
      f += ".cache"
  return os.path.join(path, f)
  
def getResource(name=''):
  return getFile('resources/', name)
  
def getDataFile(name=''):
  path = getFile("data/")
  if not os.path.isdir(path):
    os.mkdir(path)
  return getFile("data/", name)
  
def getCache(name=''):
  path = getFile("data/cache/")
  if not os.path.isdir(path):
    os.mkdir(path)
  return getFile("data/cache/", name)
