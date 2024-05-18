from .browsers import chrome 
from .browsers.browser import Browser
import time
import util
import os


flags = {
  '--remote-allow-origins': '*',
  '--no-sandbox': '',
  '--disable-gpu': '',
  '--disable-software-rasterizer': '',
}
browser: Browser = chrome.ChromeHeadless(flags=flags)

    
def screenshot(html='', output='', size=(1920, 1080)):
  if output == '':
    raise ValueError('output doesn\'t giving.')
  file = util.getCache(f'{int(time.perf_counter() * 1000)}.html')
  with open(file, 'wb') as f:
    f.write(html.encode('utf-8'))
  
  browser.screenshot(file, output, size)
  os.remove(file)
  