# tgbot
一个Telegram机器人，可以解析pixiv.net, x.com, e-hentai.org, exhentai.org, kemono.su等

demo: [@hbcao1bot](https://t.me/hbcao1bot)

## 安装
1.安装Python>=3.7

2.执行以下操作

```bash
# 1.克隆仓库或者手动下载
git clone https://github.com/HBcao233/tgbot
# 2.安装依赖
cd tgbot
pip install -r requirements.txt
# 3.运行 run
chmod 755 tgbot.sh
tgbot.sh start
# 建立快捷方式（可选）
ln -s path/to/tgbot/tgbot.sh /usr/bin/tgbot
# 查看运行状态
tgbot status
# 查看运行日志
tgbot log
# 关闭
tgbot stop
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


## 配置
重命名 `config.py.example` 为 `config.py`，按照备注修改配置

Rename `config.py.example` to `config.py`, and edit it by notes

token 必填，获取方法自行搜索 Telegram Bot Token


## 鸣谢
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
