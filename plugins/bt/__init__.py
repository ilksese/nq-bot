import os
import re
from typing import TypedDict, List
from urllib.parse import urljoin, quote

import aiohttp
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
    "bt": {
        "__HELP__": "bt [keyword]"
    }
}


baseUrl = "https://btbtt18.com/"


class BtItem(TypedDict):
    order: int
    tid: str
    name: str
    info: str
    url: str


class Attach(TypedDict):
    order: int
    file_name: str
    download: str


bt_matcher = on_regex(pattern=r"^bt", priority=10, block=True)


async def search(keyword: str) -> List[BtItem]:
    async with aiohttp.ClientSession() as client:
        async with client.get(f"{baseUrl}search-index-keyword-{quote(keyword)}.htm") as resp:
            results: List[BtItem] = []
            try:
                html_str = await resp.text()
                soup = BeautifulSoup(html_str, "html.parser")
                subjects = soup.select("#threadlist .subject")
                for index, subject in enumerate(subjects):
                    a_tag_list = subject.select(":scope > a:not(:first-child)")
                    info = ''.join(item.text for item in a_tag_list)
                    name_el = a_tag_list.pop()
                    name = name_el.text
                    url: str = urljoin(baseUrl, name_el.get("href"))
                    match_tid = re.compile("(?<=tid-)\\d+")
                    tid = match_tid.search(url).group()
                    # op(f"{name}\n{info}")
                    bt_item: BtItem = {
                        "order": index,
                        "name": name,
                        "tid": tid,
                        "info": info,
                        "url": url
                    }
                    results.append(bt_item)
            except Exception as e:
                logger.error(e)
            # logger.info(f"{keyword}\n")
            # logger.info(results)
            return results


async def into_detail_page(url: str) -> List[Attach]:
    # url = "https://btbtt18.com/thread-index-fid-1183-tid-4577186.htm"
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            soup = BeautifulSoup(await resp.content.read(), "lxml")
            attach_list_dom = soup.select(".attachlist tr td:first-child a")
            # op(attach_list_dom)
            attach_list: List[Attach] = [
                {
                    "order": index,
                    "file_name": attach_dom.text,
                    "download": urljoin(baseUrl, attach_dom.get("href"))
                } for index, attach_dom in enumerate(attach_list_dom)
            ]
    return attach_list


async def download_torrent(url: str):
    # url = "https://btbtt18.com/attach-dialog-fid-1183-aid-5278223.htm"
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            soup = BeautifulSoup(await resp.content.read(), "lxml")
            # attach-download-fid-1183-aid-5278223.htm
            file_name = soup.select_one("dl > dd:nth-of-type(1)").text
            download_link = urljoin(baseUrl, soup.select_one("dd > a").get("href"))
            # 同步模式
            # with requests.get(download_link, stream=True) as r:  # 打开流式下载连接
            #     r.raise_for_status()  # 用于检查是否发生错误，如果有则抛出异常
            #     with open('test.torrent', 'wb') as f:  # 创建一个二进制写入文件
            #         for chunk in r.iter_content(chunk_size=8192):  # 循环读取数据块
            #             if chunk:  # 如果这个数据块不为空
            #                 f.write(chunk)  # 将数据块写入文件

            # 异步模式
            async with client.get(urljoin(baseUrl, download_link)) as file_resp:
                with open(f"data/torrent/{file_name}", 'wb') as fd:
                    # iter_content：一块一块的遍历要下载的内容
                    # iter_lines：一行一行的遍历要下载的内容
                    async for chunk in file_resp.content.iter_chunked(1024):
                        fd.write(chunk)
                        fd.flush()
                        os.fsync(fd.fileno())
    return file_name


@bt_matcher.handle()
async def _(event: "GroupMessageEvent", matcher: "Matcher"):
    try:
        msg = event.get_plaintext().removeprefix("bt").strip()
        params = map(str.strip, msg.split(" "))
        keyword = next(params)
        logger.info("keyword" + keyword)
        if keyword:
            matcher.set_arg("keyword", Message([MessageSegment.text(keyword)]))
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)


@bt_matcher.got("keyword", prompt="bt: 你要搜什么呢？")
async def bt_search(
        bot: "Bot",
        event: "GroupMessageEvent",
        matcher: "Matcher",
        state: "T_State",
        keyword=ArgPlainText("keyword"),
):
    if event.get_plaintext().strip() == "qqq":
        await matcher.finish("bt: 手动结束搜索")
    if not state.get("results"):
        results: List[BtItem] = await search(keyword)
        state["results"] = results
        if len(results) == 0:
            await matcher.finish(f"bt: 没有找到{keyword}的资源，可尝试替换关键词后重新搜索")
        await send_forward_msg_group(bot, event, "飞飞飞", [
            Message([
                MessageSegment.text(f"序号: {item['order']}\n"),
                MessageSegment.text(f"《{item['name']}》\n"),
                MessageSegment.text(f"{item['info']}")
            ]) for item in state["results"]
        ])
        await matcher.reject_arg("order", "bt: 输入序号以获取对应的种子")

    order = state.get("order1") or event.get_message().extract_plain_text()
    if not str.isnumeric(order):
        await matcher.reject_arg("order", "bt: 输入序号以获取对应的种子")
    else:
        state["order1"] = order

    if not state.get("attach_list"):
        state["current"] = state["results"][int(order)]
        attach_list: List[Attach] = await into_detail_page(state["current"]["url"])
        if len(attach_list) == 0:
            await matcher.finish(f"bt: {keyword}序号{order}暂无种子，可尝试其它序号")
        state["attach_list"] = attach_list
        await send_forward_msg_group(bot, event, "飞飞飞", [
            Message([
                MessageSegment.text(f"序号: {item['order']}\n"),
                MessageSegment.text(f"{item['file_name']}"),
            ]) for item in state["attach_list"]
        ])
        await matcher.reject_arg("attach", "bt: 请选择要下载的文件")

    attach = state.get("attach") or event.get_message().extract_plain_text()
    if not str.isnumeric(attach):
        await matcher.reject_arg("attach", "bt: 请选择要下载的文件")
    else:
        state["attach"] = attach

    file_name = await download_torrent(state["attach_list"][int(state["attach"])]["download"])
    await matcher.finish(f'bt: 下载完成\n{file_name}\n查看种子: http://202.182.125.24:13501/')
