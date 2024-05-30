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
    logger.info(update.message)
    
    if not update.message or update.message.chat.type != "private":
        return
    
    asyncio.set_event_loop(loop)
    for i in config.commands:
      if i.cmd == '_':
        loop.create_task( i.func(update, context) )


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
    # logger.info(tasks)
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
       
    if len(results) > 0 or btn is not None:
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
  