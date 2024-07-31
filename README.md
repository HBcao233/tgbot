# tgbot
# 该仓库已弃用
## 本项目已用 telethon 重写,
## 新仓库地址: https://github.com/HBcao233/mtgbot
# Had Migrated to telethon
## This repo had deprecated now
## new repo: https://github.com/HBcao233/mtgbot

一个 Telegram 机器人框架

示例的 hbcao1bot 机器人可以解析 pixiv.net, x.com, e-hentai.org, exhentai.org, kemono.su 等发送至 tg

demo: [@hbcao1bot](https://t.me/hbcao1bot)

基于本框架的其他机器人: 

传话机器人: https://github.com/HBcao233/tgbot2

其他插件: https://github.com/HBcao233/tgbot-plugins

## 特别说明

如果你在GitCode (https://gitcode.com) 看到本仓库，那么请点击该网站右侧简介下的GitHub徽标访问正确的GitHub仓库。因为GitCode上的仓库是由第三方在未经授权的情况下非法创建的，他们很有可能在其中植入病毒，从而感染你的计算机，并且可能会威胁到财产安全。如果该平台要求你输入电话号码或者什么密码以完成什么操作，那么千万不要输入，这很有可能会导致你的资金被盗。

## 目录结构 Directory Structure
本框架可采取单应用架构和多应用架构两种目录结构

单应用：读取根目录下的 `.env` 和 `pligins`
```
tgbot
├ plugins: 插件存放目录
├ .env: 机器人相关配置
├ data: 运行时产生的数据
├ util: 工具类存放文件夹
├ requirements.txt: py依赖描述文件
├ tgbot.sh: 机器人管理脚本
├ main.py: 入口文件
├ config.py: 配置相关实现,
├ plugin.py: 插件相关实现
└ bot.py: bot相关实现
```

多应用架构, 拥有 `.env` 文件的目录会被判定为一个应用, 分别读取目录下的 `plugins`, 此时根目录的 `.env` 和 `pligins` 将不会读取
```
tgbot
├ hbcao1bot
  ├ plugins: 插件存放目录
  ├ .env: 机器人相关配置
  └ data: 运行时产生的数据
├ hbcao2bot
  ├ plugins: 插件存放目录
  └ env: 机器人配置
├ xxx_bot
  ├ plugins: 插件存放目录
  └ env: 机器人配置
├ util: 工具类存放文件夹
├ requirements.txt: py依赖描述文件
├ tgbot.sh: 机器人管理脚本
├ main.py: 入口文件
├ config.py: 配置相关实现,
├ plugin.py: 插件相关实现
└ bot.py: bot相关实现
```

## 安装 Installation
```
1.安装Python>=3.9

2.执行以下操作

```bash
# 1.克隆仓库或者手动下载
git clone https://github.com/HBcao233/tgbot
# 2.安装依赖
cd tgbot
pip install -r requirements.txt
```

3.（可选, 用于生成Twitter预览图）安装 google-chrome 或 chromium

```bash
# Ubantu
apt install https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# Centos
rpm -ivh https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
# 查看版本
google-chrome --version
```


## 配置 Configuration Bot
重命名 `.env.example` 为 `.env`，按照其中的注释修改配置

Rename `.env.example` to `.env`, and edit it by notes

token 必填，获取方法自行搜索 Telegram Bot Token

## 运行 How To Run
```
# 添加运行权限
chmod 755 tgbot.sh
# 启动bot
tgbot.sh start
# （可选）建立快捷方式
sudo ln -s path/to/mybot/tgbot.sh /usr/bin/mybot
# 查看运行状态
mybot status
# 查看运行日志
mybot log
# 关闭 bot
mybot stop
```

## 依赖 Dependencies
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
* [httpx](https://github.com/encode/httpx)
* [python-dotenv](https://github.com/theskumar/python-dotenv)