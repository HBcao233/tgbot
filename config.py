import os
from dotenv import load_dotenv

load_dotenv()
env = dict(os.environ)

botRoot = os.path.dirname(os.path.realpath(__file__))
commands = []
inlines = []
buttons = []

# Telegram Bot Token
token = env.get('token')
# 机器人的代理
proxy_url = None # http://127.0.0.1:10809/
if (port := env.get('proxy_port', '')) != '':
  host = 'localhost'
  if env.get('proxy_host', '') != '':
    host = env.get('proxy_host', '')
  proxy_url = f'http://{host}:{port}/'
proxies = {}
if proxy_url is not None:
  proxies.update({
    "http://": proxy_url,
    "https://": proxy_url
  })

echo_chat_id = int(env.get('echo_chat_id', 0))

base_url = env.get('base_url', 'https://api.telegram.org/bot')
base_file_url = env.get('base_file_url', 'https://api.telegram.org/file/bot')

telegraph_author_name = env.get('telegraph_author_name', '')
telegraph_author_url = env.get('telegraph_author_url', '')
telegraph_access_token = env.get('telegraph_access_token', '')

pixiv_PHPSESSID = env.get('pixiv_PHPSESSID', '')
pixiv_headers = {
  'cookie': f'PHPSESSID={pixiv_PHPSESSID}'
}

twitter_csrf_token = env.get('twitter_csrf_token', '')
twitter_auth_token = env.get('twitter_auth_token', '')
twitter_headers = {
  'content-type': 'application/json; charset=utf-8',
  'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
  'x-csrf-token': twitter_csrf_token,
  'cookie': f'auth_token={twitter_auth_token}; ct0={twitter_csrf_token}',
  'X-Twitter-Client-Language': 'zh-cn',
  'X-Twitter-Active-User': 'yes'
}

ex_ipb_member_id = env.get('ex_ipb_member_id', '')
ex_ipb_pass_hash = env.get('ex_ipb_pass_hash', '')
ex_igneous = env.get('ex_igneous', '')
ex_headers = {
  "cookie": f"ipb_member_id={ex_ipb_member_id}; ipb_pass_hash={ex_ipb_pass_hash}; igneous={ex_igneous}"
}

bili_SESSDATA = env.get('bili_SESSDATA', '')
bili_headers = {
  # 只需要 cookie 中的 SESSDATA，字段
  'cookie': f'SESSDATA={bili_SESSDATA};'
}
