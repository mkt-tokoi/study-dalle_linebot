import os

# TODO : AWS SecretManagerに移管する
LINEBOT_CHANNEL_ACCESS_TOKEN = os.environ["LINEBOT_CHANNEL_ACCESS_TOKEN"]
LINEBOT_CHANNEL_SECRET = os.environ["LINEBOT_CHANNEL_SECRET"]

# TODO  : AWS SecretManagerから取得して、！！ENVにもセットすること（for gpt-index ?）！！
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
