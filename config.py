from pydantic import BaseModel


class Config(BaseModel):
    http_proxy: str = ""
    https_proxy: str = ""
