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

import config
import util
from util.log import logger
from plugin import handler, inline_handler


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
    msg = parseTidMsg(tid, res) if not hide else 'https://x.com/i/status/' + tid
  
    if "extended_entities" not in tweet.keys():
        return await update.message.reply_text(msg, parse_mode="MarkdownV2")

    # 格式化媒体
    medias = tweet["extended_entities"]["media"]
    ms = []
    ms_a = []  # 备用
    flag = False
    for media in medias:
        if media["type"] == "photo":
            url = media["media_url_https"] + ":orig"
            img = await util.getImg(url, headers=config.twitter_headers)
            add = InputMediaPhoto(
                media=open(img, 'rb'),
                caption=msg if len(ms) == 0 else None,
                parse_mode="HTML",
                has_spoiler=mark,
            )
            ms.append(add)
            ms_a.append(add)
        else:
            variants = media["video_info"]["variants"]
            variants = list(
                filter(lambda x: x["content_type"] == "video/mp4", variants)
            )
            variants.sort(key=lambda x: x["bitrate"], reverse=True)
            url = variants[0]["url"]
            md5 = util.md5sum(string=url)
            img = await util.getImg(url, headers=config.twitter_headers, saveas=f"{md5}.mp4")
            ms.append(
                InputMediaVideo(
                    media=open(img, 'rb'),
                    caption=msg if len(ms) == 0 else None,
                    parse_mode="HTML",
                    has_spoiler=mark,
                )
            )
            if len(variants) >= 2:
                flag = True
                url = variants[1]["url"]
                ms_a.append(
                    InputMediaVideo(
                        media=url,
                        caption=msg if len(ms_a) == 0 else None,
                        parse_mode="HTML",
                        has_spoiler=mark,
                    )
                )

    # 发送
    try:
        await update.message.reply_media_group(
            media=ms, reply_to_message_id=update.message.message_id
        )
    except Exception:
        if flag:
            logger.warning('ms fail, try ms_a')
            try:
                await update.message.reply_media_group(
                    media=ms_a, reply_to_message_id=update.message.message_id
                )
            except Exception:
                flag = False
        if not flag:
            logger.info(msg)
            logger.info(json.dumps(res))
            logger.warning(traceback.format_exc())
            await update.message.reply_text("媒体发送失败")


@inline_handler(r"^(https://(twitter|x|vxtwitter|fxtwitter).com/.*/status/)?((tid|Tid|TID) ?)?\d{13,}(\?.*)?(#.*)?( ?hide ?)?( ?mark ?)?$")
async def _(update, context, query):
  text = query
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
      medias = tweet["extended_entities"]["media"]
      ms = []
      for media in medias:
          if media["type"] == "photo":
              count += 1
              results.append(
                  InlineQueryResultPhoto(
                      id=str(uuid4()),
                      photo_url=media["media_url_https"] + ":orig",
                      thumbnail_url=media["media_url_https"] + ":small",
                      caption=msg,
                      parse_mode="HTML",
                  )
              )
          else:
              count += 1
              variants = media["video_info"]["variants"]
              variants = list(
                  filter(lambda x: x["content_type"]
                         == "video/mp4", variants)
              )
              variants.sort(key=lambda x: x["bitrate"], reverse=True)
              results.append(
                  InlineQueryResultVideo(
                      id=str(uuid4()),
                      video_url=variants[0]["url"],
                      thumbnail_url=variants[-1]["url"],
                      title=msg,
                      mime_type="video/mp4",
                      caption=msg,
                      parse_mode="HTML",
                      description=f'最佳质量(bitrate: {variants[0]["bitrate"]}, 若预览图为空，请勿选择)',
                  )
              )
              if len(variants) >= 2:
                  results.append(
                      InlineQueryResultVideo(
                          id=str(uuid4()),
                          video_url=variants[1]["url"],
                          title=msg,
                          mime_type="video/mp4",
                          thumbnail_url=variants[-1]["url"],
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
    #t = dateutil.parser.parse(tweet["created_at"]) + datetime.timedelta(hours=8)
    #time = t.strftime("%Y年%m月%d日 %H:%M:%S")
    msg = (
      f'<a href="https://x.com/i/status/{tid}">{tid}</a> - '
      f'<a href="https://x.com/{user_screen_name}">{user_name}</a>:'
      f"\n{full_text}"
    )
    #f"\n\n<a href=\"https://x.com/{user_screen_name}/status/{tid}\">From X at {time}</a>\n"
    
    return msg
    