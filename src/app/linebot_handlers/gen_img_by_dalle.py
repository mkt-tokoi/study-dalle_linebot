import io
from copy import copy

import openai
import requests

from app.conf_and_cert import OPENAI_API_KEY
from app.linebot_handlers import webhook_handler, linebot_api
from linebot.models import MessageEvent, TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, \
    MessageAction, PostbackEvent
from linebot.models import (BoxComponent, BubbleContainer, FlexSendMessage,
                            ImageComponent, TextComponent, TextSendMessage, URIAction, ImageSendMessage)
import urllib.parse

openai.api_key = OPENAI_API_KEY

histories = {}


@webhook_handler.add(MessageEvent)
def handle_message(event: MessageEvent):
    history, line_user_id = get_history_for(event)

    user_msg = event.message.text

    if (user_msg in {"reset", "リセット", "クリア", "clear"}):
        reset_history(line_user_id)
        response = TextSendMessage(text='リセットしました。新しい画像について話しかけてください。')
    else:
        # 翻訳
        user_msg_eng = transcript_to_eng_if_isnt(user_msg)

        # 画像生成　3枚から選ぶ
        img_command = {
            "command": "create",
            "params": dict(
                prompt=user_msg_eng,
                n=3,
                size="1024x1024"
            )
        }
        response = generate_images(img_command, history)

    # 応答する
    linebot_api.reply_message(event.reply_token, response)


def generate_images(img_command, history):
    command_name = img_command['command']
    param = img_command['params']
    if command_name == 'create':
        img_response = openai.Image.create(**param)
    elif command_name == 'create_variation':
        param = copy(param)
        param['image'] = io.BytesIO(requests.get(param['image_url']).content)
        del param['image_url']
        img_response = openai.Image.create_variation(**param)
    else:
        raise Exception(f"Unknown image api command: {command_name}")

    return img_response_to_carousel_message(img_response, history, img_command)


def transcript_to_eng_if_isnt(user_msg):
    transcription_res = openai.Completion.create(
        engine="text-davinci-003",
        max_tokens=1000,
        prompt=f"以下の文章を英語に翻訳してください。（英語の場合はそのまま出力してください）\n---\n{user_msg}\n---\n\n英訳または元の文章：",
    )
    result = transcription_res.choices[0].text
    print(f"翻訳結果: {result}")
    return result


def img_response_to_carousel_message(img_response, history, request_command):
    columns = []
    for idx, image_item in enumerate(img_response['data']):
        image_url = image_item['url']
        history.append(image_url)
        columns.append(CarouselColumn(
            thumbnail_image_url=image_url,
            title=f'画像#{history.index(image_url)+1}',
            text='画像をクリックして保存',
            actions=[
                PostbackAction(
                    label=f'もっとこういうやつ',
                    display_text=f'もっとこういうやつ（{idx + 1}番目）',
                    data=f'history_idx={history.index(image_url)}'
                ),
            ],
            default_action=URIAction(
                label="get image",
                uri=image_url
            )
        ))

    history.append(request_command)
    more_postback_action = PostbackAction(
        label=f'他にも見る',
        display_text=f'他にも見る',
        data=f'history_idx={history.index(request_command)}'
    )
    columns.append(CarouselColumn(
        thumbnail_image_url='https://dummyimage.com/256/ffffff/000000',
        title='他にも見る',
        text='他にも見る',
        actions=[more_postback_action],
        default_action=more_postback_action,
    ))

    return TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=columns
        )
    )


def get_history_for(event):
    if hasattr(event.source, 'group_id'):
        line_user_id = event.source.group_id
    else:
        line_user_id = event.source.user_id
    history = get_history(line_user_id)
    return history, line_user_id


@webhook_handler.add(PostbackEvent)
def handle_postback(event: PostbackEvent):
    print(event)
    history, line_user_id = get_history_for(event)
    params = urllib.parse.parse_qs(event.postback.data)
    if 'history_idx' in params:
        history_idx = int(params['history_idx'][0])
        history_item = history[history_idx]

        if isinstance(history_item, str):
            # 画像のURLからバリエーションを生成
            image_url = history[history_idx]
            img_response = openai.Image.create_variation(
                image=io.BytesIO(requests.get(image_url).content),
                n=3,
                size="1024x1024"
            )
            img_command = {
                "command": "create_variation",
                "params": dict(
                    image_url=image_url,
                    n=3,
                    size="1024x1024"
                )
            }
        elif isinstance(history_item, dict):
            # 画像生成コマンドを再度実行
            img_command = history_item

        # 画像生成
        response = generate_images(img_command, history)

    else:
        response = TextSendMessage(
            text=f'Error. param history_idx not founded in data.')

    # 応答する
    linebot_api.reply_message(event.reply_token, response)


def reset_history(line_user_id):
    if line_user_id in histories:
        del histories[line_user_id]


def check_history(line_user_id):
    if line_user_id not in histories:
        histories[line_user_id] = list()


def get_history(line_user_id) -> list:
    check_history(line_user_id)
    return histories[line_user_id]
