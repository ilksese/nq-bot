import re
import asyncio
from typing import Literal
from io import BytesIO

import aiohttp
import markdown
from nonebot import on_regex, logger
from nonebot.matcher import Matcher
from nonebot.exception import MatcherException
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, Bot, GroupMessageEvent

from utils import html2image

__HELP__ = {
    "gpt": {
        "__help__": "<通用问答>\ngpt [问题]\n示例:\n\tgpt 英雄联盟亚索怎么出装",
    }
}

gpt_matcher = on_regex(pattern=r"^gpt", priority=10, block=True)

Headers = {
    "git_clone": {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://gitclone.com',
        'Pragma': 'no-cache',
        'Referer': 'https://gitclone.com/aiit/chat/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
}


async def v2(question: str) -> str:
    json_data = {
        'context': {
            'prompt': question,
            'history': [],
        },
        'modelname': 'ChatGLM-6b',
    }
    try:
        async with aiohttp.ClientSession() as client:
            stop = False
            while not stop:
                logger.info("搜索...")
                async with client.post('https://gitclone.com/aiit/codegen_stream/v2', json=json_data) as resp:
                    json_ = await resp.json()
                    stop = json_.get("stop")
                    if not isinstance(stop, bool):
                        logger.info(json_)
                        raise Exception("骚瑞，GPT炸了")
                    await asyncio.sleep(2)
        return json_.get("response")
    except Exception as e:
        raise e


async def gpt(question: str = None, ctx: bool = False, model: Literal["ChatGLM-6b"] = "ChatGLM-6b"):
    if question is None or len(str(question)) == 0:
        return None
    if model == "ChatGLM-6b":
        return await v2(question)


@gpt_matcher.handle()
async def _(bot: "Bot", matcher: "Matcher", event: "GroupMessageEvent"):
    try:
        msg = event.get_plaintext()
        await matcher.send("正在搜索...")
        answer = await gpt(question=msg.removeprefix("gpt").strip())
        if not answer:
            await matcher.finish(MessageSegment.reply(event.message_id) + "\n抱歉，没有找到答案")
        elif not await bot.can_send_image():
            await matcher.finish(Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text(answer)
            ]))
        elif len(answer) > 300 or re.search(r"```", answer):
            html_text = markdown.markdown(text=answer, extensions=["fenced_code"])
            await matcher.finish(Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.image(BytesIO(await html2image(html_text)))
            ]))
        else:
            await matcher.finish(Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text(answer)
            ]))
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)
