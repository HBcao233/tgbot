from bs4 import BeautifulSoup
import asyncio
import re 
import ujson as json

import util
import config
from util import logger


def parseEidSMsg(eid, _html):
    '''
    格式化e站s单页 msg
    '''
    soup = BeautifulSoup(_html, "html.parser")
    name = soup.select("#i1 h1")[0].string
    url = soup.select("#i3 img")[0].attrs["src"]
    sn = soup.select("#i2 .sn div")[0].text

    prev = soup.select("#i2 #prev")[0].attrs["href"]
    next = soup.select("#i2 #next")[0].attrs["href"]
    source = soup.select("#i7 a")[0].attrs["href"]
    parent = soup.select("#i5 a")[0].attrs["href"]
    return (
        f"\n<code>{name}</code>\n"
        f"{sn}\n"
        f"前：{prev}\n"
        f"后：{next}\n"
        f"原图：{source}\n"
        f"画廊：{parent}"
        f"\n\n{eid}",
        url
    )


async def parseEidGMsg(eid, soup):
    '''
    格式化e站g画廊 msg
    '''
    #name1 = soup.select("#gd2 #gn")[0].string
    title = soup.select("#gd2 #gj")[0].string
    num = soup.select("#gdd tr")[5].select(".gdt2")[
        0].text.replace(" pages", "")

    # first = soup.select("#gdt a")[0].attrs["href"]
    # r = await util.get(first, headers=config.ex_headers, proxy=True)
    # html1 = r.text
    # soup1 = BeautifulSoup(html1, "html.parser")
    # first_url = soup1.select("#i3 img")[0].attrs["src"]

    url = soup.select("#gd5 p")[2].a.attrs["onclick"].split("'")[1]
    r = await util.get(url, headers=config.ex_headers, proxy=True)
    html = r.text
    soup2 = BeautifulSoup(html, "html.parser")

    magnets = []
    for i in soup2.select("table a"):
        torrent = i.attrs["href"]
        if torrent:
            match = re.search(r"(?<=/)([0-9a-f]{40})(?=.torrent)", torrent)
            if match:
                magnet = "magnet:?xt=urn:btih:" + str(match.group())
                magnets.append(magnet)
        
    return title, num, magnets 
    
    
async def parsePage(text, soup, title, num, nocache=False, bar=None):
  num = int(num)
  if not nocache:
    try:
      r = await util.post(
        'https://api.telegra.ph/getPageList', 
        data={
          'access_token': '135fa6b60c956b336ad499fc469950acbb6ab682f9a43fbeebd42da22433',
          'limit': 200,
        }
      )
      for i in r.json()['result']['pages']:
        if i['title'] == title:
          return i['url']
    except:
      pass
  
  content = []
  urls = []
  for i in soup.select("#gdt a"):
    urls.append(i.attrs["href"])
    
  p = 1
  while len(urls) < min(num, 100):
    try:
      r = await util.get(text, params={'p': p}, headers=config.ex_headers)
      html1 = r.text
      soup1 = BeautifulSoup(html1, "html.parser")
      arr = soup1.select("#gdt a")
      if bar: await bar.add(50//min(num, 100)*len(arr))
      for i in arr:
        urls.append(i.attrs["href"])
    except Exception:
      logger.warning('未能成功获取所有p')
      break
    p += 1
  if bar: await bar.update(50)
  
  async def parse(u):
    nonlocal bar, num
    r = await util.get(u, headers=config.ex_headers)
    html1 = r.text
    soup1 = BeautifulSoup(html1, "html.parser")
    url = soup1.select("#i3 img")[0].attrs["src"]
    if bar:
      await bar.add(50//num)
    return {
      'tag': 'img',
      'attrs': {
        'src': url,
      },
    }
  
  tasks = [parse(i) for i in urls]
  for i in await asyncio.gather(*tasks):
    content.append(i)
    
  r = await util.post(
    'https://api.telegra.ph/createPage', 
    data={
      'access_token': '135fa6b60c956b336ad499fc469950acbb6ab682f9a43fbeebd42da22433',
      'title': title,
      'content': json.dumps(content),
      'author_name': '小派魔',
      'author_url': 'https://t.me/hbcao1bot'
    },
  )
  logger.info(r.text)
  if r.status_code != 200:
    return False
  res = r.json()
  if not res['ok']:
    return False
  return res['result']['url']
  