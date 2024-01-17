# tgbot
一个Telegram机器人，可以解析pixiv.net, x.com, e-hentai.org, exhentai.org, kemono.su等，demo: [@hbcao1bot](https://t.me/hbcao1bot)

## 安装
安装Python
```bash
# 1.克隆仓库或者手动下载
git clone https://github.com/HBcao233/tgbot
# 2.安装依赖
cd tgbot
pip install -r requirements.txt
# 3.运行
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

## 配置
修改config.py，只需修改有备注的地方

token 必填，获取方法自行搜索 Telegram Bot Token