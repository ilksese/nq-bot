import re
from typing import Optional, List

import requests
import urllib.parse
from pydantic import BaseModel
from bs4 import BeautifulSoup
from pygtrans import Translate, Null
from nonebot import on_regex, logger
from nonebot.matcher import Matcher
from nonebot.exception import MatcherException, FinishedException
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from utils import send_forward_msg_group

kc = on_regex(pattern=r"^kc", priority=10, block=True)
client = Translate()

__HELP__ = {
    "kc": {
        "__help__": "/kc [番号|影片|演员]",
        "magnet": {
            "__help__": "/kc magnet [番号]"
        }
    }
}


def to_jp(source):
    result = client.translate(source, target="jp")
    if isinstance(result, Null):
        logger.error("翻译失败")
        return None
    return result.translatedText


class Movie(BaseModel):
    on: Optional[str]
    title: Optional[str]
    href: Optional[str]
    pic: Optional[str]

    def from_soup(self, soup):
        img = soup.find("img")
        self.title = img.get("title")
        self.pic = img.get("src")
        self.href = soup.get("href")
        self.on = re.findall(r"(?<=www\.javbus\.com/).+$", self.href)[0]
        return self


class Javbus:
    SEARCH_COUNT = 0
    # self.action = "https://www.javbus.com/search/{0}&type=&parent=ce"
    action = "https://www.javbus.com/search/{0}/{1}&type=1"
    # 有码翻页 https://www.javbus.com/search/{搜索词}/{页码}&type=1
    # 无码 https://www.javbus.com/uncensored/search/{搜索词}&type=1
    cookies = {
        'PHPSESSID': 'qu2lq5lrhnia8ok64m2empc2r2',
        'existmag': 'all',
    }
    headers = {
        'authority': 'www.javbus.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    def __init__(self):
        pass

    @classmethod
    async def search(cls, search_value: str = "", page: int = 1, uncensored: bool = False, matcher: Matcher = None):
        cls.SEARCH_COUNT += 1
        if cls.SEARCH_COUNT > 2:
            cls.SEARCH_COUNT = 0
            return logger.info("搜索结束")
        try:
            logger.info("搜索" + search_value + "   " + cls.action.format(urllib.parse.quote(search_value), page))
            response = requests.get(
                cls.action.format(urllib.parse.quote(search_value), page),
                cookies=cls.cookies,
                headers=cls.headers
            )
            soup = BeautifulSoup(response.text, "html.parser")
            movie_boxs = soup.find_all(class_="movie-box")
            if len(movie_boxs) == 0:
                search_value_jp = to_jp(search_value)
                if matcher is not None and cls.SEARCH_COUNT < 2:
                    await matcher.send(f"沒有找到关于{search_value}的影片！尝试以{search_value_jp}重新搜索...")
                return await cls.search(search_value_jp, matcher=matcher)
            else:
                resultshowall = soup.find(id="resultshowall")
                resultshowmag = soup.find(id="resultshowmag")
                logger.info("找到{}的{}部，{}部".format(search_value, resultshowall.text, resultshowmag.text))
                movies: List[Movie] = []
                for soup in movie_boxs:
                    img = soup.find("img")
                    href = soup.get("href")
                    movies.append(Movie(**{
                        "on": re.findall(r"(?<=www\.javbus\.com/).+$", href)[0],
                        "img": soup.find("img"),
                        "title": img.get("title"),
                        "href": href,
                        "pic": img.get("src")
                    }))
                movies: list[Movie] = list(map(lambda x: Movie().from_soup(x), movie_boxs))
                return {
                    "searchValue": search_value,
                    "resultshowall": resultshowall.text,
                    "resultshowmag": resultshowmag.text,
                    "movies": movies
                }
        except Exception as e:
            logger.error(e)
            logger.error("搜索{}失败".format(search_value))


@kc.handle()
async def _(bot: "Bot", matcher: "Matcher", event: "GroupMessageEvent"):
    try:
        msg = event.get_plaintext()
        search_value = msg.removeprefix("kc").strip()
        data = await Javbus.search(search_value=search_value, matcher=matcher)
        if data is None:
            await matcher.finish("哎，没找到资源，无法开冲")
        elif isinstance(data, dict):
            msgs = ["找到{}的{}部，{}部\n下载: /kc magnet [ON]\n".format(
                data["searchValue"],
                data["resultshowall"],
                data["resultshowmag"]
            )]
            movies: List[Movie] = data["movies"]
            for movie in movies:
                msgs.append("《{}》\nON: {}\n".format(movie.title, movie.on))
            await send_forward_msg_group(bot, event, "冲娃", msgs)
            await matcher.finish("注意身体哦")
    except FinishedException:
        pass
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)
        await matcher.finish(str(e))
