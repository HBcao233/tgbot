import re
from util import logger


def parseText(text):
  hide = False
  mark = False
  origin = False
  args = text.split(" ")
  if len(args) >= 2:
      text = args[0]
      if "hide" in args or '省略' in args: hide = True
      if "mark" in args or '遮罩' in args: mark = True
      if 'origin' in args or '原图' in args: origin = True

  pid = re.sub(r"((pid|Pid|PID) ?)?", "", text)
  pid = re.sub(
      r"^(https?://)?(www.)?pixiv.net/member_illust.php?.*illust_id=", "", pid
  ).strip()
  pid = re.sub(r"((https?://)?(www.)?pixiv.net/(artworks|i)/)?", "", pid).strip()
  pid = re.sub(r"/?(\?.*)?(#.*)?", "", pid).strip()
  
  logger.info(f"{pid = }, {hide = }, {mark = }, {origin = }")
  return pid, hide, mark, origin


def parsePidMsg(res, hide=False):
  pid = res["illustId"]

  '''tags = []
  for i in res["tags"]["tags"]:
      tags.append("#" + i["tag"])
      if "translation" in i.keys():
          tags.append("#" + i["translation"]["en"])
  tags = (
      json.dumps(tags, ensure_ascii=False)
      .replace('"', "")
      .replace("[", "")
      .replace("]", "")
  )'''

  props = []
  if res["tags"]["tags"][0]["tag"] == "R-18":
      props.append('#NSFW')
  if res["tags"]["tags"][0]["tag"] == "R-18G":
      props.append('#R18G')
      props.append('#NSFW')
  if res['illustType'] == 2:
    props.append('#动图')
  if res['aiType'] == 2:
      props.append('#AI作品')
  prop = ' '.join(props)
  if prop != '':
      prop += '\n'
  
  #t = dateutil.parser.parse(res["createDate"]) + datetime.timedelta(hours=8)
  msg = prop
  msg += f"<a href=\"https://www.pixiv.net/artworks/{pid}/\">{res['illustTitle']}</a> - <a href=\"https://www.pixiv.net/users/{res['userId']}/\">{res['userName']}</a>"
  if not hide:
    comment = res["illustComment"]
    comment = (
        comment.replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
        .replace(' target="_blank"', "")
    )
    comment = re.sub(r'<span[^>]*>(((?!</span>).)*)</span>', r'\1', comment)
    if len(comment) > 400:
        comment = re.sub(r'<[^/]+[^<]*(<[^>]*)?$', '', comment[:200])
        comment = re.sub(r'\n$','',comment)
        comment = comment + '\n......'
    if comment != '':
        comment = ':\n' + comment
    msg += comment
  
  return msg