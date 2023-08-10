import time
from io import BytesIO
from typing import List

import requests
from requests_toolbelt import MultipartEncoder
from nonebot import get_driver, on_regex, logger
from utils import send_forward_msg_group
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from nonebot.exception import MatcherException
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment

hikari = on_regex(pattern="^识图", priority=10, block=True)


@hikari.handle()
async def hikari_handler(bot: "Bot", matcher: "Matcher", event: "GroupMessageEvent"):
    try:
        url = event.reply.message[0].data["url"]
        session = requests.session()
        image = session.get(url).content
        m = MultipartEncoder({
            "hide": "false",
            "image": (f"{time.time()}", BytesIO(image), "image/jpeg")
        })
        cookies = {
            'cf_clearance': '2aln4ywJ9I9.x8ADZ3LSkPTfkJWjxVBi4laiZLaptxw-1690810843-0-0.2.1690810843',
        }
        session.headers.update({
            "content-type": m.content_type,
            'authority': 'hikari.obfs.dev',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'origin': 'https://hikari.obfs.dev',
            'pragma': 'no-cache',
            'referer': 'https://hikari.obfs.dev/',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        })
        resp = session.post('https://hikari.obfs.dev/api/SauceNAO', cookies=cookies, data=m)
        if resp.status_code != 200:
            await matcher.finish("接口异常，搜图失败")
        image_info_list: List = resp.json()
        # 取前三张相似度还算高的
        message_list: List[Message] = [
            MessageSegment.image(res["image"])
            + "{}\n图片相似度: {:.2f}%\n图片来源:\n{}".format(
                res["title"],
                res["similarity"],
                "\n".join(
                    ["\n".join(dict(content).values()) for content in res["content"]]
                ),
            )
            for res in image_info_list[0:3]
        ]
        await send_forward_msg_group(bot, event, "二刺螈酱", message_list)
        await matcher.finish()
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)
        await matcher.finish("系统异常，搜图失败")