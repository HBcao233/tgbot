import traceback
import re
import util
from util import logger


class PluginException(Exception):
  pass


async def get_post(pid):
  try:
    headers={
      'origin': 'https://www.fanbox.cc',
      'referer': 'https://www.fanbox.cc/',
    }
    url = f"https://api.fanbox.cc/post.info?postId={pid}"
    r = await util.get(url, headers=headers)
  except Exception:
    logger.error(traceback.format_exc())
    raise PluginException('连接错误')
  res = r.json()
  if res.get("error", None):
    logger.error(r.text)
    raise PluginException(res["error"])
  return res['body']
  
  
def parseMsg(res):
  pid = res["id"]
  title = res['title']
  creatorId = res['creatorId']
  uid = res['user']['userId']
  username = res['user']['name']
  msg = f"<a href=\"https://{creatorId}.fanbox.cc/posts/{pid}\">{title}</a> - <a href=\"https://{creatorId}.fanbox.cc\">{username}</a>\n"
  
  body = res.get('body', None) if res.get('body', None) else {}
  text = (
    body.get('text', '')
    .replace("<br />", "\n")
    .replace("<br/>", "\n")
    .replace("<br>", "\n")
    .replace(' target="_blank"', "")
  )
  text = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', text)
  if text:
    msg += ': \n' + text
  return msg


def parseMedias(res):
  medias = []
  body = res.get('body', None) if res.get('body', None) else {}
  for i in body.get('images', []):
    media = {
      'type': 'image',
      'ext': i['extension'],
      'name': i['id'],
      'url': i['originalUrl'],
      'thumbnail': i['thumbnailUrl'],
    }
    medias.append(media)
  return medias