from linebot import LineBotApi, WebhookHandler
from app.conf_and_cert import *

# LINE Botに関するインスタンス作成
linebot_api = LineBotApi(LINEBOT_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(LINEBOT_CHANNEL_SECRET)