import asyncio
from io import BytesIO
from typing import List
from pathlib import Path

import httpx
from PIL import Image
from pydantic import BaseModel
from nonebot import on_regex, logger
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.exception import MatcherException
from nonebot.params import ArgPlainText
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment

__HELP__ = {
    "setu": {
        "__HELP__": "setu [数量=1]"
    }
}


lolicon = on_regex(pattern="^setu", priority=10, block=True)


@lolicon.handle()
async def _(bot: "Bot", event: "GroupMessageEvent", matcher: "Matcher"):
    try:
        msg = event.get_plaintext()
        params = map(str.strip, msg.removeprefix("setu").strip().split(" "))
        num = next(params)
        matcher.set_arg("num", Message([MessageSegment.text(num if num else "1")]))
    except Exception as e:
        logger.error(e)


class PixivItem(BaseModel):
    pid: int
    p: int
    uid: int
    title: str
    author: str
    r18: bool
    width: int
    height: int
    tags: List[str]
    ext: str
    aiType: int  # 0：未知 1：AI 2：非AI
    uploadDate: int
    urls: dict[str, str]


@lolicon.got("num", prompt="客官来几份儿？")
async def got_lolicon(bot: "Bot", event: "GroupMessageEvent", matcher: "Matcher", num=ArgPlainText("num")):
    try:
        if num == "q":
            await matcher.finish()
        if not num.isnumeric():
            await matcher.reject_arg("num", "客官来几份儿")
        if int(num) > 3 or int(num) < 1:
            await matcher.reject_arg("num", "数量限制1 ~ 3")
        await matcher.send(f"客官请烧等~(￣▽￣)~*")
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            json_data = {
                "r18": 0,
                "num": int(num),
                "size": "regular"
            }
            resp = await client.post(url="https://api.lolicon.app/setu/v2", headers=headers, json=json_data)
            logger.info(resp.text)
            pixiv_item_list = [PixivItem(**i) for i in resp.json()["data"]]
            for pixiv_item in pixiv_item_list:
                for quality, url in pixiv_item.urls.items():
                    desc = "title: {}\npid: {}_{}\nauthor: {}".format(
                        pixiv_item.title,
                        pixiv_item.pid,
                        pixiv_item.p,
                        pixiv_item.author
                    )
                    try:
                        resp = await client.get(url)
                        file_path = Path(f"data/lolicon/{pixiv_item.pid}_{pixiv_item.p}_{quality}.{pixiv_item.ext}")
                        await asyncio.sleep(2)
                        with Image.open(BytesIO(resp.content)) as im:
                            im.save(file_path)
                        logger.info(f"发送图片{url}")
                        await matcher.send(MessageSegment.image(resp.content) + desc)
                    except Exception:
                        logger.info(f"图片被屏蔽{url}")
                        await matcher.send(f"【图片被屏蔽】\n{desc}\n{url}")
            await matcher.finish()
    except MatcherException:
        raise
    except Exception as e:
        await matcher.finish(str(e))
