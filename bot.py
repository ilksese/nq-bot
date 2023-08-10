from pathlib import Path

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(ONEBOT_V11Adapter)

# nonebot.load_builtin_plugins('echo')


@driver.on_startup
def on_start():
    logger.info("伱群 启动！")


@driver.on_shutdown
def on_exit():
    logger.info("拜拜！")


nonebot.load_from_toml("pyproject.toml")
nonebot.load_plugin(Path("plugins/javbus/__init__.py"))
nonebot.load_plugin(Path("plugins/dmhy/__init__.py"))
nonebot.load_plugin(Path("plugins/hikari/__init__.py"))
nonebot.load_plugin(Path("plugins/lolicon/__init__.py"))
nonebot.load_plugin(Path("plugins/gpt/__init__.py"))
nonebot.load_plugin(Path("plugins/bt/__init__.py"))
nonebot.load_plugin(Path("plugins/core/__init__.py"))
# nonebot.load_plugin(Path("plugins/weather/__init__.py"))

if __name__ == "__main__":
    nonebot.run()
