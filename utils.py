import base64
import time
import urllib.parse
from pathlib import Path
from typing import List, Optional, Literal

from playwright.async_api import async_playwright


def url_encode(url):
    """
    url编码
    """
    return urllib.parse.quote(url)


def get_time():
    """获取13位时间戳"""
    return int(round(time.time() * 1000))


async def send_forward_msg_group(bot: "Bot", event: "GroupMessageEvent", name: str, msgs: "List"):
    """
    转发合并消息（群聊）
    """

    def to_json(msg):
        return {"type": "node", "data": {"name": name, "uin": bot.self_id, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    await bot.call_api(
        "send_group_forward_msg", group_id=event.group_id, messages=messages
    )


def image2base64(path_: Optional[Path] = None, image: Optional[bytes] = None) -> Optional[str]:
    """
    图片转base64
    """
    if not path_ or not image:
        return None

    ff = None
    if isinstance(path_, Path):
        f = open(path_, "rb")
        ff = base64.b64encode(f.read()).decode()
        f.close()
    elif isinstance(image, bytes):
        ff = base64.b64encode(image).decode()
    return f"base64://{ff}"


async def html2image(html_text: str, device: Literal["mobile", "pc"] = "mobile") -> bytes:
    """
    html字符串转图片
    """
    viewport = None
    if device == "mobile":
        viewport = {"width": 375, "height": 667}
    elif device == "pc":
        viewport = {"width": 1366, "height": 768}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport=viewport)
        await page.set_content(html_text)
        screenshot = await page.screenshot(full_page=True)
        await browser.close()
    return screenshot
#
#
# # aio 使用 https://juejin.cn/post/6857140761926828039
# # https://cloud.tencent.com/developer/article/1985453
# async def aio_fetch(session: aiohttp.ClientSession, url: str) -> aiohttp.ClientResponse:
#     async with session.get(url) as resp:
#         if resp.status != 200:
#             resp.raise_for_status()
#         return resp
#
#
# async def aio_network_image(url: str, headers=None, cookies=None):
#     """
#     网络图片转base64
#     """
#     # 控制并发数
#     conn = aiohttp.TCPConnector(limit=2)
#     async with aiohttp.ClientSession(headers=headers, cookies=cookies, connector=conn) as session:
#         async with session.get(url) as resp:
#             print(resp.status)
#             print(await resp.text())
