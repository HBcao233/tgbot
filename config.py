import os
import sys
from dotenv import load_dotenv

load_dotenv()
env = dict(os.environ)

token = env.get('token')
echo_chat_id = int(env.get('echo_chat_id', 0))
base_url = env.get('base_url', 'https://api.telegram.org/bot')
base_file_url = env.get('base_file_url', 'https://api.telegram.org/file/bot')

telegraph_author_name = env.get('telegraph_author_name', '')
telegraph_author_url = env.get('telegraph_author_url', '')
telegraph_access_token = env.get('telegraph_access_token', '')

botRoot = os.path.dirname(os.path.realpath(__file__))
commands = []
inlines = []
buttons = []

proxy_url = None
proxies = {}
if (port := env.get('proxy_port', '')) != '':
  host = 'localhost'
  if env.get('proxy_host', '') != '':
    host = env.get('proxy_host', '')
  config.proxy_url = f'http://{host}:{port}/'
if proxy_url is not None:
  config.proxies.update({
    "http://": proxy_url,
    "https://": proxy_url
  })
  