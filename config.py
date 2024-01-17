import os

botRoot = os.path.dirname(os.path.realpath(__file__))
commands = []
inlines = []
buttons = []

# Telegram Bot Token
token = ""
# 机器人的代理
proxy_url = None  # http://127.0.0.1:10809/
# get, post 的代理
proxies = {
    # "http://": f"http://127.0.0.1:10809/",
    # "https://": f"http://127.0.0.1:10809/"
}

pixiv_headers = {
    "Referer": "https://www.pixiv.net",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
    # Pixiv 的 Cookie, 只需要 PHPSESSID 字段
    "cookie": "PHPSESSID=",
}

twitter_headers = {
    'content-type': 'application/json; charset=utf-8',
    # Twitter 的 authorization
    'authorization': '',
    # Twitter 的 x-csrf-token
    'x-csrf-token': '',
    # Twitter 的 cookie
    'cookie': '',
    'X-Twitter-Client-Language': 'zh-cn',
    'X-Twitter-Active-User': 'yes'
}

ex_headers = {
  # exhentai 的 cookie, 只需要 ipb_member_id, ipb_pass_hash, igneous 字段
  "cookie": "ipb_member_id=; ipb_pass_hash=; igneous="
}

fanbox_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
    # Fanbox 的 Cookie, 只需要 FANBOXSESSID 字段
    "cookie": "FANBOXSESSID=",
}