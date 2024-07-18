from .utils import fetch
from typing import Union
from . import subtitle
import re
import base64
import json
import logging
import asyncio
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

async def get_imdb_info(imdb: str) -> str:
    api_url = "https://api.themoviedb.org/3/find/" + imdb + "?api_key=0f020a66f3e35379eef31c31363f2176&external_source=imdb_id"
    req = await fetch(api_url, {
        "Host" : "api.themoviedb.org",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    req_data = req.json()
    return req_data
