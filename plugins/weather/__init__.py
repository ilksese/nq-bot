import os
import re
from typing import TypedDict, List

import aiohttp
import asyncio
import requests
from objprint import op
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup


baseUrl = "https://btbtt18.com/"

class BtItem(TypedDict):
    order: int
    tid: str
    name: str
    info: str
    url: str


async def search(search_value: str) -> List[BtItem]:
    async with aiohttp.ClientSession() as client:
        async with client.get(f"{baseUrl}search-index-keyword-{quote(search_value)}.htm") as resp:
            results: List[BtItem] = []
            try:
                html_str = await resp.text()
                soup = BeautifulSoup(html_str, "html.parser")
                subjects = soup.select("#threadlist .subject")
                for index, subject in enumerate(subjects):
                    a_tag_list = subject.select(":scope > a:not(:first-child)")
                    name_el = a_tag_list.pop()
                    name = name_el.text
                    url: str = name_el.get("href")
                    info = ''.join(item.text for item in a_tag_list)
                    # op(f"{name}\n{info}")
                    match_tid = re.compile("(?<=tid-)\\d+")
                    bt_item: BtItem = {
                        "order": index,
                        "name": name,
                        "tid": match_tid.search(url).group(),
                        "info": ''.join(item.text for item in a_tag_list),
                        "url": urljoin(baseUrl, url)
                    }
                    results.append(bt_item)
            except Exception as e:
                op(e)
            op(results)
            return results

class Attach(TypedDict):
    title: str
    href: str


async def into_detail_page(url: str) -> List[Attach]:
    # url = "https://btbtt18.com/thread-index-fid-1183-tid-4577186.htm"
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            soup = BeautifulSoup(await resp.content.read(), "lxml")
            attach_list_dom = soup.select(".attachlist tr td:first-child a")
            # op(attach_list_dom)
            attach_list: List[Attach] = [
                {
                    "title": attach_dom.text,
                    "href": urljoin(baseUrl, attach_dom.get("href"))
                } for attach_dom in attach_list_dom
            ]
    op(attach_list)
    return attach_list


async def download_torrent():
    url = "https://btbtt18.com/attach-dialog-fid-1183-aid-5278223.htm"
    async with aiohttp.ClientSession() as client:
        async with client.get(url) as resp:
            soup = BeautifulSoup(await resp.content.read(), "lxml")
            # attach-download-fid-1183-aid-5278223.htm
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
                with open("test.torrent", 'wb') as fd:
                    # iter_content：一块一块的遍历要下载的内容
                    # iter_lines：一行一行的遍历要下载的内容
                    async for chunk in file_resp.content.iter_chunked(1024):
                        fd.write(chunk)
                        fd.flush()
                        os.fsync(fd.fileno())

if __name__ == '__main__':
    asyncio.run(download_torrent())
