import asyncio
import os
import sys

import config
from bot import main


loop = config.loop


if __name__ == "__main__":
  path = sys.argv[1] if len(sys.argv) > 1 else None
  path = path.replace('./', '')
  config.botName = path
  config.workPath = os.path.dirname(os.path.realpath(__file__))
  path = os.path.join(config.workPath, path)
  config.botRoot = path
  if not os.path.isdir(path) or not os.path.isfile(os.path.join(path, '.env')):
    print(f'"{path}" is not a bot dir')
    exit(1)
    
  config.init(path)
  config.loop.run_until_complete(main(path))
  try:
    config.loop.run_forever()
  finally:
    config.loop.close()
    