import os.path
import cv2
import time 
import numpy as np
from .log import logger
from .file import getCache


def videoInfo(path):
  cap = cv2.VideoCapture(path)
  rate = cap.get(5)
  frame_count = cap.get(7)
  duration = frame_count / rate
  width = cap.get(3)
  height = cap.get(4)
  ret, img = cap.read(1)
  thumbnail = getCache(f'{round(time.time())}.jpg')
  getPhotoThumbnail(img, saveas=thumbnail)
  cap.release()
  _thumbnail = open(thumbnail, 'rb')
  os.remove(thumbnail)
  return open(path, 'rb'), duration, width, height, _thumbnail


def getPhotoThumbnail(path, saveas=None) -> cv2.Mat:
  return resizePhoto(path, 320, saveas=saveas)
  
  
def resizePhoto(path, maxSize=2560, size=None, saveas=None) -> cv2.Mat:
  if isinstance(path, cv2.Mat):
    img = path
  else:
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
  h, w, channels = img.shape
  if size is None:
    if w >= h:
      size = (maxSize, int(maxSize * h / w))
    else:
      size = (int(maxSize * w / h), maxSize)
  img = cv2.resize(img, size)
  if channels == 4:
    white = np.zeros(img.shape, dtype='uint8') 
    img = cv2.add(img, white)
  if saveas is not None:
    cv2.imwrite(saveas, img)
  return img
  