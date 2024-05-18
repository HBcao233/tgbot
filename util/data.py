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
    