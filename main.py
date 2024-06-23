import asyncio
import telegram
import re
from telegram import (
  Update, 
  BotCommand,
  BotCommandScopeChat,
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
from plugin import load_plugins, handler

import nest_asyncio
nest_asyncio.apply()
loop = asyncio.new_event_loop()


def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  logger.error(
    msg="Exception while handling an update:",
    exc_info=context.error
  )


def callback(context):
  def _(task):
    context.user_data['tasks'].remove(task)
  return _
  
  
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
  
  if context.user_data.get('tasks', None) is None:
    context.user_data['tasks'] = []
  
  asyncio.set_event_loop(loop)
  for i in config.commands:
    if i.cmd == '_':
      task = loop.create_task( i.func(update, context, text) )
      task.add_done_callback(callback(context))
      context.user_data['tasks'].append(task)
      
  for i in config.commands:
    if (
      text 
      and (
        (i.private_pattern is not None and str(message.chat.type) == "private" and re.search(i.private_pattern, text))
        or (i.pattern is not None and re.search(i.pattern, text))
      )
    ):
      task = loop.create_task( i.func(update, context, text) )
      task.add_done_callback(callback(context))
      context.user_data['tasks'].append(task)
      return


async def echo(update, context) -> None:
  message = update.message
  # logger.info(message)
  if message and message.chat.type == "private":
    logger.info(f'chat_id: {message.chat.id}, message_id: {message.id}')
    if (attr := getattr(message, 'photo', None)):
      logger.info(f'photo file_id: {attr[-1].file_id}')
    for i in ['video', 'audio', 'document', 'sticker']:
      if (attr := getattr(message, i, None)):
        logger.info(f'{i} file_id: {attr.file_id}')
  
  asyncio.set_event_loop(loop)
  for i in config.commands:
    if i.cmd == '_':
      loop.create_task( i.func(update, context) )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    for i in config.buttons:
      if re.search(i.pattern, query.data):
        return loop.create_task( i.func(update, context, query) )


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
      

@handler('cancel', info='取消当前任务')
async def cancel(update, context, text):
  import inspect
  tasks = context.user_data.get('tasks', [])
  if not len(tasks):
    return await update.message.reply_text('当前没有进行中的任务')
  
  flag = True
  for i in tasks:
    logger.info(f'取消任务: {id(i)}')
    i.cancel()
    c = i.get_coro().cr_frame
    c = inspect.getargvalues(c).locals
    
    if (m := c.get('mid', None)):
      await update.message.reply_text(
        f'取消任务 {id(i)}',
        reply_to_message_id=m.message_id,
      )
      flag = False
  if flag:
    await update.message.reply_text('已取消所有任务')
  context.user_data['tasks'] = []
  
  
@handler('start')
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
  if len(text) <= 0:
    for i in config.commands:
      if i.cmd == 'help':
        await i.func(update, context)
        break
    return 
  text = text.replace("_", " ").strip()
  logger.info(f"start: {text}")
  await handle(update, context, text)
    
    
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
    if i.cmd != '':
      app.add_handler(CommandHandler(i.cmd, i.func))
  
  app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO | filters.Document.ALL | filters.AUDIO | filters.Sticker.ALL, echo))
  app.add_handler(MessageHandler(filters.TEXT, handle))
  app.add_handler(InlineQueryHandler(inline_query))
  app.add_handler(CallbackQueryHandler(button))

  commands = []
  for i in config.commands:
    if i.info != "" and i.scope != 'superadmin':
      commands.append(BotCommand(i.cmd, i.info))
  await bot.set_my_commands(commands)
  
  for i in config.commands:
    if i.info != "" and i.scope == 'superadmin':
      commands = [BotCommand(i.cmd, i.info)] + commands
  for i in config.superadmin:
    scope = BotCommandScopeChat(chat_id=i)
    await bot.set_my_commands(commands, scope=scope)
    
  await app.initialize()
  await app.start()
  await app.updater.start_polling()
    
    
if __name__ == "__main__":
  loop.run_until_complete(main())
  loop.run_forever()
  