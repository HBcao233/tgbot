import qrcode
import time
import asyncio

import util
import config
from plugins.bili.auth import appsign


async def main():
  r = await util.post(
    'https://passport.snm0516.aisee.tv/x/passport-tv-login/qrcode/auth_code',
    headers=config.bili_headers,
    params=appsign(),
  )
  print(r.text)
  res = r.json()['data']
  url = res['url']
  auth_code = res['auth_code']
  
  qr = qrcode.QRCode()
  qr.add_data(url)
  qr.print_ascii(invert=True)
  
  input('请扫码登录后回车以继续...')
  
  r = await util.post(
    'https://passport.snm0516.aisee.tv/x/passport-tv-login/qrcode/poll',
    headers=config.bili_headers,
    params=appsign({
      'auth_code': auth_code,
    }),
  )
  print(r.text)
  res = r.json()
  if res['code'] != 0:
    return print(f"二维码未登录或已失效: {res['code']}")
  print(f"登录成功, access_token: {res['data']['access_token']}")

if __name__ == '__main__':
  asyncio.run(main())
  