import re

import requests
from bs4 import BeautifulSoup
from nonebot import on_regex, logger
from nonebot.matcher import Matcher
from nonebot.exception import MatcherException
from nonebot.params import ArgPlainText
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, Bot, GroupMessageEvent
from nonebot.typing import T_State

from utils import send_forward_msg_group

__HELP__ = {
    "zy": {
        "__help__": "zy [关键词] [类型]",
    }
}

zy = on_regex(pattern=r"^zy", priority=10, block=True)
zy_types = {
    "0": "全部",
    "1": "其他",
    "2": "动画",
    "3": "漫画",
    "4": "音乐",
    "6": "日剧",
    "7": "RAW",
    "9": "游戏",
    "12": "特摄",
    "q": "退出"
}


@zy.handle()
async def zy_handler(state: "T_State", matcher: "Matcher", event: "GroupMessageEvent"):
    try:
        msg = event.get_plaintext()
        params = map(str.strip, msg.removeprefix("zy").strip().split(" "))
        keyword = next(params, False)
        sort_id = next(params, False)
        state["user_id"] = event.user_id
        if keyword:
            matcher.set_arg("keyword", Message([MessageSegment.text(keyword)]))
        if sort_id:
            matcher.set_arg("sort_id", Message([MessageSegment.text(sort_id)]))
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)


def zy_type_text() -> str:
    result = ""
    for key in zy_types.keys():
        result = f"{result}{key}: {zy_types[key]}\n"
    return result


@zy.got("keyword", prompt="资源的名字是？")
@zy.got("sort_id", prompt=f"请选择一个类型\n{zy_type_text()}")
async def got_zy(bot: Bot, event: GroupMessageEvent, keyword=ArgPlainText("keyword"), sort_id=ArgPlainText("sort_id")):
    if sort_id == "q":
        await zy.finish()
    if not zy_types.get(sort_id):
        await zy.reject_arg("sort_id", "不支持的类型，请重试")
    # 发起请求，在动漫花园搜索
    await zy.send(f"正在搜索关于{keyword}的{zy_types.get(sort_id)}内容")
    api = f"https://dmhy.org/topics/rss/rss.xml?keyword={keyword}&sort_id={sort_id}&team_id=0&order=date-desc"
    resp = requests.get(api)
    rss_xml = BeautifulSoup(resp.content, "xml")
    # 限制解析数量，加快速度
    item_list = rss_xml.find_all("item", limit=3)
    if len(item_list) == 0:
        return await zy.finish(f"没有在{zy_types[sort_id]}分类中找到有关{keyword}的内容")
    msg_list = []
    for item in item_list:
        title = item.find("title").text
        category = item.find("category").text
        magnet = item.find("enclosure").get("url")
        magnet = re.match(r"^(magnet:\?xt=urn:btih:[0-9a-zA-Z]+)(?=&)", magnet)
        msg_list.append(f"{title}\n【{category}】\n{'' if not magnet else magnet.group()}")
    await send_forward_msg_group(bot, event, "二次元怎么你了", msg_list)
    await zy.finish()
