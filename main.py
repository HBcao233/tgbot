import asyncio
import telegram
import re
import traceback
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        message = update.edited_message

    text = (
        message["text"]
        .replace("@"+config.bot.username, "")
        .replace("/start", "")
        .strip()
    )
    if text[0] == "/":
        return
      
    for i in config.commands:
      if i.private_pattern is not None and str(message.chat.type) == "private" and re.search(i.private_pattern, text):
          return await i.func(update, context)
      if i.pattern is not None and re.search(i.pattern, text):
          return await i.func(update, context)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #print(update.message)
    bot = context.bot

    if update.message and update.message.chat.type != "private":
        return
      
    message = update.message
    logger.info(message)
    if message.photo:
        res = await bot.getFile(file_id=message.photo[-1].file_id)
        await message.reply_text(
            f'<code>{message.photo[-1].file_id}</code>\n' + 
            re.sub('api.telegram.org/file/[^/]+/', 'tgapi.hbcao.top/', res.file_path), 
            reply_to_message_id=update.message.message_id,
            parse_mode='HTML',
        )
    if message.video:
        try:
            res = await bot.getFile(file_id=message.video.file_id)
            await message.reply_text(
                f'<code>{message.video.file_id}</code>\n' + 
                re.sub('api.telegram.org/file/[^/]+/', 'tgapi.hbcao.top/', res.file_path), 
                reply_to_message_id=update.message.message_id,
                parse_mode='HTML',
            )
        except Exception:
            logger.error(traceback.print_exc())
            await message.reply_text(
                f'<code>{message.video.file_id}</code>', 
                reply_to_message_id=update.message.message_id,
                parse_mode='HTML',
            )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    for i in config.buttons:
      if re.search(i.pattern, query.data):
        return await i.func(update, context, query)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query."""
    query: str = update.inline_query.query
    if not query:
        return

    for i in config.inlines:
      if re.search(i.pattern, query):
        return await i.func(update, context, query)
  
  
@handler('start')
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    #logger.info(update.message)
    logger.info(f"start: {text}")

    if len(text) <= 0:
        await help(update, context)
    update.message["text"] = update.message["text"].replace('-', ' ')
    await handle(update, context)


@handler('help')
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
        "/pid <url/pid>: 获取p站作品\n"
        "/tid <url/tid>: 获取推文\n"
        "/eid <url>: e站爬取\n"
        "/kid <url>: kemono爬取\n"
        "/help: 查看本帮助信息\n"
        "小提示: 以上命令都可以省略 /, 私聊可直接发送url/pid/tid: 自动识别可进行的爬取\n"
        "附加参数:\n"
        "hide: 隐藏作品描述\n"
        "mark/遮罩: 给爬取到的图片添加遮罩\n"
        "origin/原图: 发送原图",
        reply_markup=reply_markup,
    )
    
    
async def main(app):
    bot: telegram.Bot = app.bot
    config.bot = await bot.get_me()
    
    
if __name__ == "__main__":
  app = (
      ApplicationBuilder()
      .token(config.token)
      .proxy_url(config.proxy_url)
      .get_updates_proxy_url(config.proxy_url)
      .build()
  )
  asyncio.run(main(app))
  app.add_error_handler(error_handler)
  
  load_plugins('plugins')
  for i in config.commands:
    app.add_handler(CommandHandler(i.cmd, i.func))
  
  app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO, echo))
  app.add_handler(MessageHandler(filters.TEXT, handle))
  app.add_handler(InlineQueryHandler(inline_query))
  app.add_handler(CallbackQueryHandler(button))

  app.run_polling()  # 启动Bot