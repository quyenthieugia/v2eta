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
executor = ThreadPoolExecutor(max_workers=10)

async def handle_server(imdb_id) -> dict:
    # GET SERVER
    req = await fetch("https://embed.smashystream.com/dataaw.php?imdb="+imdb_id, {
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

async def handle_link_in_thread(url: str) -> dict:
    loop = asyncio.get_event_loop()
    # Run handle_link in a separate thread
    return await loop.run_in_executor(executor, handle_link, url)

async def handle_link(url: str) -> dict:
    try:
        logging.debug(f"Fetching URL: {url}")
        req = await fetch(url, {
            "Referer": "https://player.smashy.stream/",
            "Origin": "https://player.smashy.stream",
            "Host": "smashystream.top",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Sec-Fetch-Site": "cross-site",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        })
        req_data =  req.json()  # Ensure to await the JSON parsing
        logging.debug(f"Received data: {req_data}")
        return req_data
    except Exception as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return ""
    
    
async def get_server(dbid: str, s: int = None, e: int = None) -> dict:
    try:
        id_url = f"https://embed.smashystream.com/dataad.php?imdb={dbid}" + (f"&season={s}&episode={e}" if s and e else '')
        print(id_url)
        logging.debug(f"Fetching server data from URL: {id_url}")
        req = await fetch(id_url, {
            "Referer": "https://player.smashy.stream/",
            "Host": "embed.smashystream.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Sec-Fetch-Site": "cross-site"
        })
        req_data = req.json()  # Ensure to await the JSON parsing
        logging.debug(f"Received server data: {req_data}")

        url_array = req_data.get("url_array", [])  # Ensure url_array exists
        sources = []
        stream = []
        async def fetch_source(item):
            source_data = await handle_link(item.get('url', ''))
            if source_data != "" :
                sources.append(source_data)

        await asyncio.gather(*[fetch_source(item) for item in url_array])
        for source in sources:
            source_urls = source['sourceUrls']
            for url in source_urls:
                result = decrypt(url)
                stream.append(result)
        RESULT = {
            'result': {
                #'data': req_data,
                'sources': stream
            }
        }
        return RESULT
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return {'result': None}

async def get_source(url:str):
    RESULT = {}
    RESULT['result'] = await handle_source(url)
    return RESULT

def b1(s):
    return base64.b64encode(urllib.parse.quote(s).encode('utf-8')).decode('utf-8')

def b2(s):
    return urllib.parse.unquote(base64.b64decode(s).decode('utf-8'))

def decrypt(x):
    a = x[2:]
    v = {
        "bk0": "vXch5/GNVBbrXO/Xt", "bk1": "qxO/5lMkx/N5Gjv5J", "bk2": "OVw/M39ryrfCs/yO5", "bk3": "eeAd/OwcV07/Wgo7T", "bk4": "UN/35mMFQjt3/9vst"
    }
    for i in range(4, -1, -1):
        if v[f"bk{i}"] != "":
            a = a.replace("///" + b1(v[f"bk{i}"]), "")

    try:
        data = b2(a)
        v1 = "0"
        v2 = "."
        v3 = "/"
        v4 = "m3u8"
        v5 = "5"
        data = re.sub(r"\{v1\}", v1, data, flags=re.IGNORECASE)
        data = re.sub(r"\{v2\}", v2, data, flags=re.IGNORECASE)
        data = re.sub(r"\{v3\}", v3, data, flags=re.IGNORECASE)
        data = re.sub(r"\{v4\}", v4, data, flags=re.IGNORECASE)
        data = re.sub(r"\{v5\}", v5, data, flags=re.IGNORECASE)
        return data
    except Exception as e:
        print(f"Error: {e}")
        # libs.log({'e': e}, PROVIDER, 'ERROR')
    return ""
