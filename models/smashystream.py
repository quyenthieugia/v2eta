from .utils import fetch
from typing import Union
from . import subtitle
import re
import base64

async def handle_server(imdb_id) -> dict:
    # GET SERVER
    req = await fetch("https://embed.smashystream.com/dataaa.php?imdb="+imdb_id, {
        "Referer": "https://player.smashy.stream/",
        "Host" : "embed.smashystream.com",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Sec-Fetch-Site" : "cross-site"
    })
    req_data = req.json()
    return {
            'data': req_data
        }

async def handle_source(url) -> dict:
    # GET SERVER
    req = await fetch(url, {
        "Referer": "https://player.smashy.stream/",
        "Origin": "https://player.smashy.stream",
        "Host" : "embed.smashystream.com",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Sec-Fetch-Site" : "cross-site",
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    req_data = req.json()
    return {
            'data': req_data
        }
    
async def get_server(imdb_id:str):
    RESULT = {}
    RESULT['result'] = await handle_server(imdb_id)
    return RESULT

async def get_source(url:str):
    RESULT = {}
    RESULT['result'] = await handle_source(url)
    return RESULT