import asyncio
import telegram
import re
import traceback
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyParameters,
    InputMediaPhoto,
    InputMediaVideo,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    InlineQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

import config
import util
from util.log import logger
from plugin import handler, load_plugins

import nest_asyncio
nest_asyncio.apply()
loop = asyncio.new_event_loop()

def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None) -> None:
    message = update.message
    if not message:
        message = update.edited_message
    # logger.info(message)
    if text is None:
      text = (
        message.text
        .replace("@"+config.bot.username, "")
        .replace("/start", "")
        .strip()
      )
    if text[0] == "/":
      return
    
    asyncio.set_event_loop(loop)
    for i in config.commands:
      if i.private_pattern is not None and str(message.chat.type) == "private" and re.search(i.private_pattern, text):
          loop.create_task( i.func(update, context, text) )
          return
      if i.pattern is not None and re.search(i.pattern, text):
          loop.create_task( i.func(update, context, text) )
          return


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # logger.info(update.message)
    bot = context.bot

    if update.message and update.message.chat.type != "private":
        return
      
    message = update.message
    logger.info(message)
    
    if getattr(message, 'media_group_id', None):
      if not context.bot_data.get('media_group', None): context.bot_data['media_group'] = {}
      if not context.bot_data['media_group'].get(message.media_group_id, None): 
        context.bot_data['media_group'][message.media_group_id] = []
        context.job_queue.run_once(echo_timer, 1, data=message.media_group_id)
      context.bot_data['media_group'][message.media_group_id].append(message)
      return

    if message.photo or message.video or message.document or message.audio:
      if config.echo_chat_id != 0:
        message = await bot.forwardMessage(chat_id=config.echo_chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
        logger.info(message)

    if message.photo:
        await update.message.reply_text(
            f'<code>p_{message.photo[-1].file_id}</code>', 
            reply_to_message_id=update.message.message_id,
            parse_mode='HTML',
        )
    if message.video:
        await update.message.reply_text(
            f'<code>vi_{message.video.file_id}</code>', 
            reply_to_message_id=update.message.message_id,
            parse_mode='HTML',
        )
    if message.document:
        await update.message.reply_text(
            f'<code>d_{message.document.file_id}</code>', 
            reply_to_message_id=update.message.message_id,
            parse_mode='HTML',
        )
    if message.audio:
        await update.message.reply_text(
            f'<code>au_{message.audio.file_id}</code>', 
            reply_to_message_id=update.message.message_id,
            parse_mode='HTML',
        )

async def echo_timer(context):
  # logger.info(context.job.data)
  ms = context.bot_data.get('media_group', {}).get(context.job.data, [])
  res = []
  for m in ms:
    if m.photo:
      res.append("p_" + m.photo[-1].file_id)
    elif m.video:
      res.append("vi_" + m.video.file_id)
  res = list(map(lambda x : "<code>" + x + "</code>", res))
  await context.bot.sendMessage(
      chat_id=ms[0].chat.id,
      text="\n".join(res), 
      reply_to_message_id=ms[0].message_id,
      parse_mode='HTML',
  )
  if 'media_group' in context.bot_data.keys() and context.job.data in context.bot_data['media_group'].keys():
    del context.bot_data['media_group'][context.job.data]


_file_pattern = r"(vi_|p_|d_|au_)([a-zA-Z0-9-_]+)"
@handler("file", private_pattern=_file_pattern)
async def file(update, context, text):
    bot = context.bot
    r = re.findall(_file_pattern, text)
    # r = list(map(lambda x: list(filter(lambda y: y!='', x)), r))
    logger.info(r)

    ms = []
    async def _s():
      nonlocal ms, bot
      if len(ms) > 0:
        await bot.sendMediaGroup(chat_id=update.message.chat_id, media=ms, reply_parameters=ReplyParameters(message_id=update.message.message_id, chat_id=update.message.chat_id))
        ms = []
    
    for i in r:
      try:
        if i[0] == 'p_':
          ms.append(InputMediaPhoto(media=i[1]))
          # await bot.sendPhoto(chat_id=update.message.chat_id, photo=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'vi_':
          ms.append(InputMediaVideo(media=i[1]))
          # await bot.sendVideo(chat_id=update.message.chat_id, video=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'd_':
          await _s()
          await bot.sendDocument(chat_id=update.message.chat_id, document=i[1], reply_to_message_id=update.message.message_id)
        elif i[0] == 'au_':
          await _s()
          await bot.sendAudio(chat_id=update.message.chat_id, audio=i[1], reply_to_message_id=update.message.message_id)
      except Exception:
        logger.error(traceback.print_exc())
        bot.sendMessage(chat_id=update.message.chat.id, text="Error, maybe non-existent", reply_to_message_id=update.message.message_id)
    await _s()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    for i in config.buttons:
      if re.search(i.pattern, query.data):
        return loop.create_task( i.func(update, context, query) )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query."""
    query: str = update.inline_query.query
    if query is None : return
    tasks = []
    for i in config.inlines:
      if re.search(i.pattern, query):
        task = i.func(update, context, query)
        if i.block:
          return loop.create_task(task)
        else: 
          tasks.append(task)
    logger.info(tasks)
    results = []
    btn = None
    if len(tasks) > 0:
      for res, _btn in (await asyncio.gather(*tasks)):
        if type(res) == list:
          results.extend(res)
        else:
          results.append(res)
        if _btn is not None:
          btn = _btn
       

    if len(results) > 0 or len(btn) > 0:
      await update.inline_query.answer(
          results,
          cache_time=10,
          button=btn,
      )
  
@handler('start')
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    if len(text) <= 0:
        return await help(update, context)
    text = text.replace("_", " ").strip()
    logger.info(f"start: {text}")
    await handle(update, context, text)


@handler('help', info='介绍与帮助')
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE, text=''):
    keyboard = [
        [
            InlineKeyboardButton("源代码", url=f"https://github.com/HBcao233/tgbot"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await update.message.reply_text(
        "Hi! 这里是小派魔! \n"
        "指令列表: \n"
        "/pid <url/pid>: 获取p站作品 (类似 @Pixiv_bot\n"
        "/tid <url/tid>: 获取推文 (类似 @TwPicBot\n"
        "/eid <url>: e站爬取\n"
        "/kid <url>: kemono爬取\n"
        "小提示: 私聊可直接发送url/pid/tid: 自动识别可进行的爬取\n"
        "/roll [min=0][ -~/][max=9]: 返回一个min~max的随机数（默认0-9）\n",
        reply_markup=reply_markup,
    )
    
    
async def main():
  app = (
      ApplicationBuilder()
      .token(config.token)
      .proxy(config.proxy_url)
      .get_updates_proxy(config.proxy_url)
      .base_url(config.base_url)
      .base_file_url(config.base_file_url)
      .build()
  )
  bot: telegram.Bot = app.bot
  config.bot = await bot.get_me()
  app.add_error_handler(error_handler)

  load_plugins('plugins')
  for i in config.commands:
    app.add_handler(CommandHandler(i.cmd, i.func))
  
  app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO | filters.Document.ALL | filters.AUDIO, echo))
  app.add_handler(MessageHandler(filters.TEXT, handle))
  app.add_handler(InlineQueryHandler(inline_query))
  app.add_handler(CallbackQueryHandler(button))

  commands = []
  for i in config.commands:
    if i.info != "":
      commands.append(BotCommand(i.cmd, i.info))
  await bot.set_my_commands(commands)
  
  await app.initialize()
  await app.start()
  await app.updater.start_polling()
    
    
if __name__ == "__main__":
  loop.run_until_complete(main())
  loop.run_forever()