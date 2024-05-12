import asyncio
import hashlib
import random
import re
import ujson as json
import httpx
import traceback
import os.path
from typing import Union
import urllib.parse

import config
from util.log import logger


async def request(
    method, url, *, params=None, data=None, proxy=False, headers=None, **kwargs
):
    p = urllib.parse.urlparse(url)
    _headers = {
       "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
       'Referer': p.scheme + '://' + p.netloc + '/',
       'host': p.netloc,
    }
    headers = dict(_headers, **headers) if headers else None
    client = httpx.AsyncClient(
        proxies=config.proxies if proxy else None, 
        verify=False
    )
    # logger.info(headers)
    
    r = await client.request(
      method, url=url, headers=headers, data=data, params=params, **kwargs
    )
    
    if params is None: params = dict()
    if type(params) == dict: params = urllib.parse.urlencode(params)
    params = params.strip()
    if params != '':
      if '?' in url:
        url += '&' + params
      else:
        url += '?' + params
    if r.status_code == 302:
      url = r.headers['Location']
      if 'http' not in url: url = p.scheme + '://' + p.netloc + '/' + url
      r = await client.request(
        method, url=url, headers=headers, data=data, **kwargs
      )
    logger.info(f"{method} {url} code: {r.status_code}")
    await client.aclose()
    return r


async def get(url, *, proxy=False, headers=None, params=None, data=None, **kwargs):
    return await request(
        "GET", url, params=params, data=data, proxy=proxy, headers=headers, **kwargs
    )


async def post(url, *, proxy=False, headers=None, params=None, data=None, **kwargs):
    return await request(
        "POST", url, params=params, data=data, proxy=proxy, headers=headers, **kwargs
    )


async def getImg(
    url, *, proxy=True, cache=True, path=None, headers=None, rand=False, ext=False, saveas=None, **kwargs
) -> str:
    """
    获取下载广义上的图片，可以为任意文件

    Args:
        url: 图片url，或图片bytes
        proxy: 是否使用代理
        path: 保存路径， 不填默认为 data/cache/{md5(url)}.cache
        headers: 指定headers，如 p站图片需要{"Referer": "https://www.pixiv.net"}
        rand: 是否在文件结尾加入随机字符串bytes
        ext: 自动从url中获取文件后缀名
        saveas: 重命名

    Returns:
        str: 图片路径
    """
    if not os.path.exists('data/cache'): os.makedirs('data/cache')
    b = isinstance(url, bytes)
    url_tip = f'{url if not b else ""}{"bytes" if b else ""}'
    logger.info(f"尝试获取图片 (proxy:{proxy}, headers:{headers}) {url_tip}")

    if not b and url.find("file://") >= 0:
        if path is None:
            path = url[7:]
        if rand:
            with open(path, "ab") as f:
                f.write(randStr().encode())
        logger.info(f"获取图片成功: {path}")
        await asyncio.sleep(0.001)
        return path

    if b:
        md5 = md5sum(byte=url)
        gopath = f"/data/cache/{md5}.cache"
        if path is None:
            path = config.botRoot + gopath
        with open(path, "wb") as f:
            f.write(url)

        if rand:
            with open(path, "ab") as f:
                f.write(randStr().encode())

        logger.info(f"获取图片成功: {path}")
        return path
    else:
        md5 = md5sum(string=url)
        if not saveas:
            gopath = f"/data/cache/{md5}.cache"
            if ext and '.' in url:
                ex = url.split(".")[-1]
                ex = re.sub(r"(\?.*)?(#.*)?(:.*)?", "", ex)
                gopath = f"/data/cache/{md5}.{ex}"
        else:
            if ext:
              arr = saveas.split('.')
              ex = url.split(".")[-1]
              ex = re.sub(r"(\?.*)?(#.*)?(:.*)?", "", ex)
              if '.' in saveas:
                arr[-1] = ex
              else:
                arr.append(ex)
              saveas = '.'.join(arr)
            gopath = f"/data/cache/{saveas}"
        if path is None:
            path = config.botRoot + gopath
        
        if not saveas and os.path.isfile(config.botRoot + f"/data/cache/{md5}.png"):
            path = config.botRoot + f"/data/cache/{md5}.png"
        
        if not os.path.isfile(path) or not cache:
            p = urllib.parse.urlparse(url)
            _headers = {
               "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1517.62",
               'Referer': p.scheme + '://' + p.netloc + '/',
               'host': p.netloc,
            }
            headers = dict(_headers, **headers) if headers else None
            async with httpx.AsyncClient(
              proxies=config.proxies if proxy else None, 
              verify=False,
              timeout=httpx.Timeout(connect=None, read=None, write=None, pool=None),
              http2=True,
            ) as client:
              async with client.stream(
                'GET', url=url, headers=headers,
              ) as r:
                with open(path, "wb") as f:
                  async for chunk in r.aiter_raw():
                    f.write(chunk)

            if rand:
                with open(path, "ab") as f:
                    f.write(randStr().encode())

        logger.info(f"获取图片成功: {path}")
        return path
        

def randStr(length: int = 8) -> str:
    """
    随机字符串

    Args:
        length: 字符串长度, 默认为 8

    Returns:
        str: 字符串
    """
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    res = ""
    for i in range(length):
        res += random.choice(chars)
    return res


def md5sum(
    string: Union[str, bytes] = None, byte: bytes = None, file_path: str = None
) -> str:
    """
    计算字符串或文件的 md5 值

    Args:
        string: 字符串（三选一）
        byte: bytes（三选一）
        file_path: 文件路径（三选一）

    Returns:
        str: md5
    """
    if string:
        if isinstance(string, bytes):
            return hashlib.md5(string).hexdigest()
        return hashlib.md5(string.encode()).hexdigest()
    if byte:
        return hashlib.md5(byte).hexdigest()
    if file_path:
        with open(file_path, "rb") as fp:
            data = fp.read()
        return hashlib.md5(data).hexdigest()
    return ""


def getData(file: str) -> dict:
  path = config.botRoot+f'/data/{file}.json'
  if not os.path.isfile(path):
    setData(file, dict())
  with open(path, 'r') as f:
    data = f.read()
    if data == '': data = '{}'
    data = json.loads(data)
    return data
    
def setData(file: str, data: dict):
  with open(config.botRoot+f'/data/{file}.json', 'w') as f:
    f.write(json.dumps(data))
    