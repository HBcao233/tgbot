import re
import traceback
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InlineQueryResultVideo,
    InlineQueryResultsButton,
    InputTextMessageContent,
    InlineQueryResultPhoto,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
)
from telegram.ext import ContextTypes
import dateutil.parser
import datetime
import urllib.parse
import ujson as json
from uuid import uuid4
import os.path

import config
import util
from util.log import logger
from plugin import handler, inline_handler
import util.html2image as html2image

@handler('tid',
  private_pattern=r"^((https?://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?\d{13,}(.*)$",
  pattern=r"^((tid|Tid|TID) ?)((https?://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?\d{13,}(.*)$",
  info="获取推文 /tid <url/tid> [hide] [mark]"
)
async def tid(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    hide = False
    mark = False
    args = text.split(" ")
    if len(args) >= 2:
        text = args[0]
        if "hide" in args:
            hide = True
        if "mark" in args or '遮罩' in args:
            mark = True
    logger.info(f"text: {text}, hide: {hide}, mark: {mark}")

    tid = re.sub(
        r"tid|Tid|TID", "", text
    ).strip()
    tid = re.sub(
        r"(https?://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/(\d{13,})/?.*", r"\3", tid).strip()
    logger.info(f"tid: {tid}")
    if tid == "":
        return await update.message.reply_text(
            "用法: /tid <url/tid> [hide] [mark]\n"
            "tid/url: 推文链接或status_id\n"
            "hide: 隐藏信息，推文内容将只显示推文链接\n"
            "mark: 添加遮罩\n"
            "私聊小派魔时可以省略/tid，直接发送<url/tid> [hide] [mark]哦\n"
            "或者使用@hbcao1bot <url/tid> [hide] [mark]作为内联模式发送~",
            reply_to_message_id=update.message.message_id,
        )

    res = await get_twitter(tid)
    if type(res) == str:
        return await update.message.reply_text(res)
    if 'tombstone' in res.keys():
        logger.info(json.dumps(res))
        return await update.message.reply_text(res['tombstone']['text']['text'])
    
    tweet = res["legacy"]
    msg, full_text = parseTidMsg(tid, res) if not hide else 'https://x.com/i/status/' + tid
    
    if "extended_entities" not in tweet.keys():
        return await update.message.reply_text(msg, parse_mode="MarkdownV2")

    # 格式化媒体
    medias = parseMedias(tweet)
    ms = []
    videos = util.getData('videos')
    for media in medias:
      if media["type"] == "photo":
        url = media["url"]
        md5 = media['md5']
        img = await util.getImg(
          url, 
          headers=config.twitter_headers,
          saveas=f"{md5}.png"
        )
        photo = open(img, 'rb')
        add = InputMediaPhoto(
          media=photo,
          caption=msg if len(ms) == 0 else None,
          parse_mode="HTML",
          has_spoiler=mark,
        )
        ms.append(add)
      else:
        url = media["url"]
        md5 = media['md5']
        if not (video := videos.get(md5, None)):
          img = await util.getImg(
            url, 
            headers=config.twitter_headers, 
            saveas=f"{md5}.mp4"
          )
          video = open(img, 'rb')
        add = InputMediaVideo(
          media=video,
          caption=msg if len(ms) == 0 else None,
          parse_mode="HTML",
          has_spoiler=mark,
        )
        ms.append(add)
    
    flag = False
    try:
      img = await getPreview(res, full_text, medias)
    except Exception:
      logger.warning(traceback.format_exc())
    else: 
      flag = True
      ms[0]._unfreeze()
      ms[0].caption = None
      add = InputMediaPhoto(
        media=open(img, 'rb'),
        caption=msg,
        parse_mode="HTML",
        has_spoiler=mark,
      )
      ms = [add] + ms
      
    # 发送
    try:
      m = await update.message.reply_media_group(
        media=ms, 
        reply_to_message_id=update.message.message_id,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60,
        pool_timeout=60,
      )
      if flag:
        m = m[1:]
      for i, ai in enumerate(m):
        md5 = medias[i]['md5']
        #if getattr(ai, 'photo', None) and not photos.get(md5s[i], None):
        #  photos[md5s[i]] = ai.photo[-1].file_id
        
        if getattr(ai, 'video', None) and not videos.get(md5, None):
          videos[md5] = ai.video.file_id
      # util.setData('photos', photos)
      util.setData('videos', videos)
    except Exception:
      logger.info(msg)
      logger.info(json.dumps(res))
      logger.warning(traceback.format_exc())
      await update.message.reply_text("媒体发送失败")


@inline_handler(r"^(https://(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?((tid|Tid|TID) ?)?\d{13,}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$")
async def _(update, context, text):
  results = []
  hide = False
  mark = False
  args = text.split(" ")
  if len(args) >= 2:
      text = args[0]
      if "hide" in args or '省略' in args: hide = True
      if "mark" in args or '遮罩' in args: mark = True
      if 'origin' in args or '原图' in args: origin = True
  logger.info(f"text: {text}, hide: {hide}, mark: {mark}")

  tid = re.sub(
      r"((https://)?(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?((tid|Tid|TID) ?)?", "", text
  ).strip()
  tid = re.sub(r"(\?.*)?(#.*)?", "", tid).strip()
  logger.info(f"tid: {tid}")
  if tid == "":
      return

  res = await get_twitter(tid)
  if type(res) == str:
      logger.info(res)
      return await update.inline_query.answer([])

  tweet = res["legacy"]
  msg = parseTidMsg(tid, res, hide)
  count = 0
  if "extended_entities" in tweet.keys():
      medias = parseMedias(tweet)
      ms = []
      for media in medias:
          if media["type"] == "photo":
              count += 1
              results.append(
                  InlineQueryResultPhoto(
                      id=str(uuid4()),
                      photo_url=media["url"],
                      thumbnail_url=media["thumbnail_url"],
                      caption=msg,
                      parse_mode="HTML",
                  )
              )
          else:
              count += 1
              results.append(
                  InlineQueryResultVideo(
                      id=str(uuid4()),
                      video_url=media["url"],
                      thumbnail_url=media["thumbnail_url"],
                      title=msg,
                      mime_type="video/mp4",
                      caption=msg,
                      parse_mode="HTML",
                      description=f'最佳质量(bitrate: {variants[0]["bitrate"]}, 若预览图为空，请勿选择)',
                  )
              )
              variants = media['variants']
              if len(variants) >= 2:
                  results.append(
                      InlineQueryResultVideo(
                          id=str(uuid4()),
                          video_url=variants[1]["url"],
                          title=msg,
                          mime_type="video/mp4",
                          thumbnail_url=media["thumbnail_url"],
                          caption=msg,
                          parse_mode="HTML",
                          description=f'较高质量(bitrate: {variants[1]["bitrate"]})',
                      )
                  )
  else:
      count += 1
      results.append(
          InlineQueryResultArticle(
              id=str(uuid4()),
              title=msg,
              input_message_content=InputTextMessageContent(
                  msg, parse_mode="HTML"
              ),
          )
      )
      
  
  countFlag = count > 1
  btn_text = "获取" + ("遮罩" if mark else "全部") + ("原图" if origin else "图片") + ("(隐藏描述)" if hide else "")
  start_parameter = f"{tid}_{'hide' if hide else ''}_{'mark' if mark else ''}_{'origin' if origin else ''}"
  logger.info(f"btn_text: {btn_text}, start: {start_parameter}")
  button = InlineQueryResultsButton(
      text=btn_text,
      start_parameter=start_parameter,
  ) if countFlag or mark else None
  await update.inline_query.answer(
      results,
      cache_time=10,
      button=button,
  )
  

async def get_twitter(tid):
    url = "https://twitter.com/i/api/graphql/NmCeCgkVlsRGS1cAwqtgmw/TweetDetail"
    variables = {
        "focalTweetId": str(tid),
        "with_rux_injections": False,
        "includePromotedContent": True,
        "withCommunity": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withBirdwatchNotes": True,
        "withVoice": True,
        "withV2Timeline": True,
    }
    features = {
        "rweb_lists_timeline_redesign_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": False,
        "tweet_awards_web_tipping_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_media_download_video_enabled": False,
        "responsive_web_enhance_cards_enabled": False,
    }
    data = urllib.parse.urlencode(
        {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
        }
    )
    try:
        r = await util.get(
            url, params=data, headers=config.twitter_headers, proxy=True, timeout=60
        )
        tweet_detail = r.json()
        if "errors" in tweet_detail.keys() and len(tweet_detail["errors"]) > 0:
            if tweet_detail["errors"][0]["code"] == 144:
                return "推文不存在"
            return tweet_detail["errors"][0]["message"]

        entries = tweet_detail["data"]["threaded_conversation_with_injections_v2"][
            "instructions"
        ][0]["entries"]
        tweet_entrie = list(
          filter(lambda x: x["entryId"] == f"tweet-{tid}", entries)
        )[0]
        tweet_result = tweet_entrie["content"]["itemContent"]["tweet_results"]["result"]
        if "tweet" in tweet_result.keys():
            return tweet_result["tweet"]
        else:
            return tweet_result
    except json.JSONDecodeError:
        return f"未找到tid为{tid}的推文"
    except Exception:
        logger.warning(traceback.format_exc())
        return "连接超时"


def parseTidMsg(tid, res):
    tweet = res["legacy"]
    user = res["core"]["user_results"]["result"]["legacy"]

    full_text = tweet["full_text"]
    if "urls" in tweet["entities"].keys():
        for i in tweet["entities"]["urls"]:
            full_text = full_text.replace(i["url"], i["expanded_url"])
    full_text = re.sub(r"\s*https:\/\/t\.co\/\w+$", "", full_text)
    full_text = re.sub(
        r"#([^ \n]+)", r'<a href="https://x.com/hashtag/\1">#\1</a>', full_text
    )
    full_text = re.sub(
        r"@(\w*)", r'<a href="https://x.com/\1">@\1</a>', full_text)

    user_name = user["name"]
    user_screen_name = user["screen_name"]
    t = dateutil.parser.parse(tweet["created_at"]) + datetime.timedelta(hours=8)
    time = t.strftime("%Y年%m月%d日 %H:%M:%S")
    msg = (
      f'<a href="https://x.com/{user_screen_name}/status/{tid}">{time}</a>\n'
      f'<a href="https://x.com/{user_screen_name}">{user_name}</a>'
    )
    if full_text != '':
      msg += f":\n{full_text}"
    #f"\n\n<a href=\"https://x.com/{user_screen_name}/status/{tid}\">From X at {time}</a>\n"
    
    return msg, full_text
    
def parseMedias(tweet):
  res = []
  medias = tweet["extended_entities"]["media"]
  for media in medias:
    if media["type"] == "photo":
      res.append({
        'type': 'photo',
        'url': media["media_url_https"] + ":orig",
        'md5': util.md5sum(media["media_url_https"] + ":orig"),
        'thumbnail_url': media["media_url_https"] + ":small",
      })
    else:
      variants = media["video_info"]["variants"]
      variants = list(
        filter(lambda x: x["content_type"] == "video/mp4", variants)
      )
      variants.sort(key=lambda x: x["bitrate"], reverse=True)
      url = variants[1]["url"] if len(variants) > 1 else variants[0]["url"]
      res.append({
        'type': 'video',
        'url': url,
        'md5': util.md5sum(url),
        'thumbnail_url': variants[-1]["url"],
        'variants': variants,
      })
  return res
  
    
async def getPreview(res, full_text, medias):
  import cv2
  
  tweet = res["legacy"]
  user = res["core"]["user_results"]["result"]["legacy"]
  # logger.info(tweet)
  tid = tweet['id_str']
  name = user['name']
  username = '@' + user['screen_name']
  profile = user['profile_image_url_https']
  profile_img = await util.getImg(profile)
  
  medias_html = ''
  logger.info(medias)
  for media in medias:
    ai = media['md5']
    img = util.getCache(ai)
    if not os.path.isfile(img):
      await util.getImg(media['url'])
    if media['type'] == 'photo':
      medias_html += f'<div class="media"><img src="{img}" /></div>'
    else:
      cap = cv2.VideoCapture(img)
      ret, frame = cap.read()
      img = util.getCache(ai + '_preview.jpg')
      cv2.imwrite(img, frame)
      cap.release()
      medias_html += f'''<div class="media"><img src="{img}" /><img class="video" src="{config.botRoot + '/resources/video.png'}"/></div>'''
  logger.info(medias_html)
  
  html = (
    '''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    ::-webkit-scrollbar {
      display: none;
    }
    * {
     padding: 0;
     margin: 0;
     font-family: SimSun;
     font-size: 25px;
    }
    .tweet { 
      width: 100vw; 
      padding: 30px;
    }
    .tweet .head, .tweet .body { 
      width: calc(100% - 60px); 
      height: auto; 
    }
    .tweet .head {
      display: flex;
      flex-direction: row;
    }
    .box {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      overflow: hidden;
    } 
    .box img {width:100%;height:100%;}
    .userinfo {
      height: 80px;
      margin-left: 10px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .userinfo .nickname, .userinfo .username {
      max-width: 200px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    .userinfo .nickname {
      font-weight: bold;
    }
    .body {
      padding: 0 5px;
    }
    .medias {
      width: calc(100% - 10px);
      height: 400px;
      overflow: hidden;
      border-radius: 25px;
      font-size: 0;
      display: grid;
      grid-auto-flow: row dense;
      grid-template-columns: repeat(2, 50%);
      grid-template-rows: repeat(2, 50%);
      grid-gap: 5px;
    }
    .medias .media {
      position: relative;
      display: block;
      width: 100%;
      height: 100%;
      border: 1px solid #eee;
      overflow: hidden;
      grid-column-end: span 2;
      grid-row-end: span 2;
    }
    .media img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .medias:has(> .media:nth-child(2)) > .media {
      grid-column-end: span 1;
    }
    
    .medias:has(> .media:nth-child(3)) > .media {
      grid-row-end: span 1;
    }
    .medias:has(> .media:nth-child(3)) > .media:nth-child(1) {
      grid-row-end: span 2;
    }
    
    .medias:has(> .media:nth-child(4)) > .media {
      grid-column-end: span 1;
      grid-row-end: span 1;
    }
    
    .medias .media .video {
      display: inline-block;
      position: absolute;
      width: 50px;
      height: 50px;
      top: 50%;
      left: 50%;
      -webkit-transform: translate(-50%, -50%);
      border: none;
      margin: 0;
    }
    </style></head>'''
    f'''<body>
    <div class="tweet">
      <div class="head">
        <div class="box"><img src="{profile_img}" /></div>
        <div class="userinfo">
          <div class="nickname">{name}</div>
          <div class="username">{username}</div>
        </div>
      </div>
      <div class="body">
        <div class="content">{full_text}</div>
        <div class="medias">{medias_html}<div>
      </div>
    </div>
  </body></html>'''
  )
  filename = f"t{tid}.jpg"
  f = util.getCache(filename)
  html2image.screenshot(html, f, (500, 700))
  return f