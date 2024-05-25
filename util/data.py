import ujson as json
import os.path
from .file import getDataFile


def getData(file: str) -> dict:
  path = getDataFile(f'{file}.json')
  if not os.path.isfile(path):
    setData(file, dict())
  with open(path, 'r') as f:
    data = f.read()
    if data == '': data = '{}'
    data = json.loads(data)
    return data
    
def setData(file: str, data: dict):
  with open(getDataFile(f'{file}.json'), 'w') as f:
    f.write(json.dumps(data, indent=4))
    
    
class Data(object):
  def __init__(self, file: str):
    self.file = file
    self.data = getData(file)
    
  def __getitem__(self, key, default=None):
    return self.data.get(key, default)
    
  def __setitem__(self, key, value):
    self.data[key] = value
    
  def save(self):
    setData(self.file, self.data)
    
  def __enter__(self):
    return self
    
  def __exit__(self, type, value, trace):
    self.save()

class Photos(Data):
  def __init__(self):
    super().__init__('photos')

class Videos(Data):
  def __init__(self):
    super().__init__('videos')

class Documents(Data):
  def __init__(self):
    super().__init__('documents')
