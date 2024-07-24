import sys
import os.path
from dotenv import load_dotenv


class Config:
  commands = []
  inlines = []
  buttons = []
  
  def __init__(self):
    pass
  
  def init(self, path):
    load_dotenv(dotenv_path=os.path.join(path, '.env'))
    self.env = os.environ
    self.token = self.env.get('token')
    self.base_url = self.env.get('base_url', 'https://api.telegram.org/bot')
    self.base_file_url = self.env.get('base_file_url', 'https://api.telegram.org/file/bot')
    local_mode = self.env.get('local_mode', False)
    self.local_mode = True if local_mode in ['1', 'true', 'True', 'T'] else False
    
    self.echo_chat_id = int(e) if (e := self.env.get('echo_chat_id', '')) else 0
    self.superadmin = [int(x) for x in self.env.get('superadmin', '').split(',') if x]
    
    self.telegraph_author_name = self.env.get('telegraph_author_name', '')
    self.telegraph_author_url = self.env.get('telegraph_author_url', '')
    self.telegraph_access_token = self.env.get('telegraph_access_token', '')
    
    self.proxy_url = None
    self.proxies = {}
    if (port := self.env.get('proxy_port', '')) != '':
      host = 'localhost'
      if self.env.get('proxy_host', '') != '':
        host = self.env.get('proxy_host', '')
      self.proxy_url = f'http://{host}:{port}/'
    
      proxy_user = self.env.get('proxy_user', '')
      proxy_pass = self.env.get('proxy_pass', '')
      if proxy_user and proxy_pass:
          self.proxy_url = f'http://{proxy_user}:{proxy_pass}@{host}:{port}'
          
    if self.proxy_url is not None:
      self.proxies.update({
        "http://": self.proxy_url,
        "https://": self.proxy_url
      })
    
sys.modules[__name__] = Config()
