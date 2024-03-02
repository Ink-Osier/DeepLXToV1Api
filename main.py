import os
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import aiohttp
import asyncio
import logging
from typing import List
import datetime
import json
import uuid
import time 

logging.basicConfig(level=logging.INFO)

from starlette.middleware.base import BaseHTTPMiddleware

class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 读取请求体内容
        body = await request.body()
        
        # 记录请求路径和请求体
        logging.debug(f"Request path: {request.url.path}")
        logging.debug(f"Request body: {body}")
        
        # 继续处理请求
        response = await call_next(request)
        return response

app = FastAPI()

# 添加中间件到应用
app.add_middleware(LogRequestsMiddleware)

class ChatRequest(BaseModel):
    messages: List[dict]
    stream: bool
    model: str

async def translate_single(text: str, source_lang: str, target_lang: str, session: aiohttp.ClientSession):
    if source_lang == target_lang:
        return {target_lang: text}

    # url = "https://api.deeplx.org/translate"
    # url 从环境变量获取
    url = os.environ.get("TRANSLATION_API_URL", "https://api.deeplx.org/translate")
    payload = {}
    if source_lang == "":
        payload = {
            "text": text,
            "target_lang": target_lang
        }
    else:
        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }

    start_time = time.time()
    async with session.post(url, json=payload) as response:
        logging.info(f"Translation from {source_lang} to {target_lang} took: {time.time() - start_time}")
        if response.status != 200:
            logging.error(f"Translation failed: {response.status}, {await response.text()}")
            raise HTTPException(status_code=response.status, detail="Translation failed")

        result = await response.json()
        if result['code'] != 200:
            logging.error(f"Translation failed: {result}")
            raise HTTPException(status_code=400, detail="Translation failed")

        return {target_lang: result['data']}
    
from fastapi.encoders import jsonable_encoder

@app.post("/v1/chat/completions")
async def translate_request(chat_request: ChatRequest):
    request_data = jsonable_encoder(chat_request)
    logging.info(f"Received request: {request_data}")

    model_split = chat_request.model.split('-')
    # 检查 model_split 的长度，以适应不同情况
    if len(model_split) == 3:
        source_lang = model_split[1]
        target_lang = model_split[2]
    elif len(model_split) == 2:
        source_lang = ""  # 将 source_lang 置为空
        target_lang = model_split[1]
    else:
        # 如果 model_split 长度既不是 2 也不是 3，记录错误并返回
        logging.error(f"Invalid model format: {chat_request.model}")
        return Response(content="Invalid model format.", status_code=400)

    text = ""
    for message in chat_request.messages:
        if message['role'] == 'user':
            # text = message['content'][0]
            content = message.get('content', "")
            if isinstance(content, list):
                text = content[0]
            else:
                text = content

    if text == "":
        logging.warning("No user message found.")
        return Response(content="No user message found.", status_code=400)

    logging.info(f"Translating from {source_lang} to {target_lang}, text: {text}")


    async def sse_translate():
        chat_message_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().timestamp()

        async with aiohttp.ClientSession() as session:
            translation_result = await translate_single(text, source_lang, target_lang, session)

            translated_text = translation_result.get(target_lang, "")
            data = {
                "id": chat_message_id,
                "object": "chat.completion.chunk",
                "created": timestamp,
                "model": chat_request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": translated_text
                        },
                        "finish_reason": None
                    }
                ]
            }
            logging.info(f"Translated text: {translated_text}")
            yield f"data: {json.dumps(data)}\n\n"

        # 在所有翻译数据发送完成后发送结束信号
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_translate(), media_type="text/event-stream")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
