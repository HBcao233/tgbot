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
        # BotCommand("done", "发送图片后输入，完成并转发"),
        # BotCommand("cancel", "取消发送并清除当前缓存"),
        BotCommand("pid", "获取p站作品, 用法 /pid <url/pid> [hide] [mark]"),
        BotCommand("tid", "获取推文, 用法 /tid <url/tid> [hide] [mark]"),
        BotCommand("kid", "kenomo爬取, 用法 /kid <url> [hide] [mark]"),
        BotCommand("eid", "e站爬取, 用法 /eid <url> [hide] [mark]"),
        # BotCommand("set", "绑定qq, 用法"),
        # BotCommand("q", "将回复消息做成贴纸~")
    ]
    async with bot:
        print(await bot.get_me())
        await bot.set_my_commands(commands)


if __name__ == '__main__':
    asyncio.run(main())
