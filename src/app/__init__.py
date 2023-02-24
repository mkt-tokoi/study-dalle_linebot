import os
from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse
from linebot.exceptions import InvalidSignatureError
from starlette.exceptions import HTTPException
import app.linebot_handlers as linebot_handlers
import app.linebot_handlers.gen_img_by_dalle  # ハンドラのロード。これがないと、ハンドラが登録されないので消さないこと

# FastAPIのインスタンス作成
fast_api = FastAPI(title="study/dall.e_linebot", description="")

@fast_api.get(path="/",
              summary="For connectivity test only (GET)")
async def index():
    return FileResponse("static/index.html")


@fast_api.post(path="/",
               summary="For connectivity test only (POST))")
async def index_post():
    return FileResponse("static/index.html")


@fast_api.post(path="/callback",
               summary="Callback handler for LINE Message API")
async def callback(request: Request, x_line_signature=Header(None)):
    body = await request.body()

    try:
        linebot_handlers.webhook_handler.handle(body.decode("utf-8"), x_line_signature)
        return "OK"
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="InvalidSignatureError")
