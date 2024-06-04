import os.path
import config
import cv2
import time 


def getFile(dir_name='', name=''):
  name = str(name)
  path = os.path.join(config.botRoot, dir_name)
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
  return getFile("data/cache/", name)


def videoInfo(path):
  cap = cv2.VideoCapture(path)
  rate = cap.get(5)
  frame_count = cap.get(7)
  duration = frame_count / rate
  width = cap.get(3)
  height = cap.get(4)
  ret, img = cap.read(1)
  h, w, channels = img.shape
  if w >= h:
    size = (320, int(320 * h / w))
  else:
    size = (int(320 * w / h), 320)
  img = cv2.resize(img, size)
  thumbnail = getCache(f'{round(time.time())}.jpg')
  cv2.imwrite(thumbnail, img)
  cap.release()
  _thumbnail = open(thumbnail, 'rb')
  os.remove(thumbnail)
  return open(path, 'rb'), duration, width, height, _thumbnail
