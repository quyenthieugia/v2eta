import asyncio
from bs4 import BeautifulSoup
from . import F2Cloud,filemoon
from .utils import fetch,error,decode_url



async def get(source_url:str):
    RESULT = {}
    RESULT['data'] = await F2Cloud.handle_futoken(source_url)
    return RESULT
    

