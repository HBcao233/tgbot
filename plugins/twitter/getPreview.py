import cv2
import math
import os.path
import re

import util
import util.string as string
from util.log import logger
import util.html2image as html2image


async def getPreview(res, medias, full_text, time):
  tweet = res["legacy"]
  user = res["core"]["user_results"]["result"]["legacy"]
  # logger.info(tweet)
  tid = tweet['id_str']
  name = user['name']
  username = '@' + user['screen_name']
  profile = user['profile_image_url_https']
  profile_img = await util.getImg(profile)
  
  full_text = full_text.replace('\n', '<br>')
  arr = full_text.split('<br>')
  line = len(arr)
  for i in arr:
    i = re.sub(r'<a[^>]*>(((?!</a>).)*)</a>', r'\1', i)
    width = string.width(i)
    add = math.ceil(width / 42) - 1 
    if add > 0: 
      line += add
    logger.info(f'{i = }, {add = }')
  logger.info(f'{line = }')
  
  medias_html = ''
  video_icon = util.getResource('video_icon.png')
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
      medias_html += f'''<div class="media"><img src="{img}" /><img class="video" src="{video_icon}"/></div>'''
  #logger.info(medias_html)
  
  html = (
    '''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    ::-webkit-scrollbar {
      display: none;
    }
    * {
     padding: 0;
     margin: 0;
     font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
     font-size: 50px;
     color: rgb(15, 20, 25);
     font-weight: 400;
    }
    .tweet { 
      width: 100vw; 
      padding: 60px;
      box-sizing: border-box;
    }
    .tweet .head, .tweet .body { 
      width: 100%; 
      height: auto; 
    }
    .tweet .head {
      display: flex;
      flex-direction: row;
    }
    .box {
      width: 160px;
      height: 160px;
      border-radius: 50%;
      overflow: hidden;
    } 
    .box img {width:100%;height:100%;}
    .userinfo {
      height: 160px;
      margin-left: 20px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .userinfo .nickname, .userinfo .username {
      max-width: 400px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
    .userinfo .nickname {
      font-weight: 700;
    }
    .userinfo .username {
      color: rgb(83, 100, 113);
    }
    .body {
      padding: 0 10px;
      margin-top: 40px;
      font-weight: 500;
    }
    .medias {
      margin-top: 40px;
      width: 100%;
      height: 1200px;
      overflow: hidden;
      border-radius: 50px;
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
    
    .medias:has(> .media:nth-child(4)) > .media:nth-child(1) {
      grid-row-end: span 1;
    }
    
    .medias .media .video {
      display: inline-block;
      position: absolute;
      width: 100px;
      height: 100px;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      border: none;
      margin: 0;
    }
    .time {
      margin-top: 20px;
      font-size: 40px;
      color: rgb(83, 100, 113);
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
        <div class="medias">{medias_html}</div>
        <div class="time">{time}</div>
      </div>
    </div>
  </body></html>'''
  )
  filename = f"t{tid}.jpg"
  f = util.getCache(filename)  
  html2image.screenshot(html, f, (1200, 1600+line*60)) 
  return f
  