import asyncio

from telegram import BotCommand
from telegram.ext import ApplicationBuilder
import config

async def main():
    app = (
        ApplicationBuilder()
        .token(config.token)
        .proxy_url(config.proxy_url)
        .get_updates_proxy_url(config.proxy_url)
        .build()
    )
    bot = app.bot
    commands = [
        BotCommand("help", "介绍与帮助"),
        BotCommand("pid", "获取p站作品 /pid <url/pid> [hide] [mark]"),
        BotCommand("tid", "获取推文 /tid <url/tid> [hide] [mark]"),
        BotCommand("kid", "kenomo爬取 /kid <url> [hide] [mark]"),
        BotCommand("eid", "e站爬取 /eid <url> [hide] [mark]"),
        BotCommand("roll", "生成随机数 /roll [min=0] [max=9]")
    ]
    async with bot:
        print(await bot.get_me())
        await bot.set_my_commands(commands)


if __name__ == '__main__':
    asyncio.run(main())
