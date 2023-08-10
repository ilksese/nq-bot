from typing import Optional

from nonebot import get_driver, on_regex, logger
from nonebot.matcher import Matcher
from nonebot.exception import MatcherException
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .config import Config
from ..gpt import __HELP__ as GPT_HELP
from ..javbus import __HELP__ as JAVBUS_HELP
from ..dmhy import __HELP__ as DMHY_HELP
from ..lolicon import __HELP__ as SETU_HELP
from ..bt import __HELP__ as BT_HELP

global_config = get_driver().config
config = Config.parse_obj(global_config)

# 1. 日排行【默认】
# 2. 周排行
# 3. 月排行
# 4. 原创排行
# 5. 新人排行
# 6. R18日排行
# 7. R18周排行
# 8. R18受男性欢迎排行
# 9. R18重口排行【慎重！】
# /prk [*分类序号] [数量] [日期]
# /prk搜图 [*关键词] [数量] [排序方式] [r18]
# pixiv [pid]
#     支持链接解析https://www.pixiv.net/artworks/(\d+)|illust_id=(\d+)
# /[识图|以图搜图]（回复包含图片的消息）
#     saucenao搜图（默认）、ascii2d搜图
#     ehentai搜图、tracemoe搜图、iqdb搜图
# /资源 [日剧动画|音乐|漫畫]
# /search（@bot）
__HELP__ = '''\
伱群Bot V1.1
gpt [*问题]
kc [*关键词]
zy [关键词] [类型]
setu [数量=1]
bt [keyword]
/随个人
/磁力搜索 [*搜索词]
'''

help_dict = {
    "help": {
        "__help__": __HELP__,
        **DMHY_HELP,
        **SETU_HELP,
        **GPT_HELP,
        **JAVBUS_HELP,
        **BT_HELP
    }
}


def get_help(cmd: str) -> Optional[str]:
    if len(cmd.strip()) == 0:
        return None
    cmd = [item.strip() for item in cmd.split(" ")]
    help_value = None
    for item in cmd:
        if help_value is None:
            help_value = help_dict.get(item)
        else:
            help_value = help_value.get(item)
    return help_value and help_value.get("__help__")


help_matcher = on_regex(pattern=r"^help", priority=10, block=True)


@help_matcher.handle()
async def _(matcher: "Matcher", event: "GroupMessageEvent"):
    try:
        msg = event.get_plaintext().strip()
        await matcher.finish(get_help(msg))
    except MatcherException:
        raise
    except Exception as e:
        logger.error(e)
        await matcher.finish(str(e))
