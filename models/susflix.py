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
import random
import bmemcached
from concurrent.futures import ThreadPoolExecutor
#memcache_client = base.Client(('localhost', 11211))
memcache_client = bmemcached.Client(('127.0.0.1:11211'),username='admin',password='Daodinh215186')
async def get_imdb_info(imdb: str) -> str:
    api_url = "https://api.themoviedb.org/3/find/" + imdb + "?api_key=0f020a66f3e35379eef31c31363f2176&external_source=imdb_id"
    req = await fetch(api_url, {
        "Host" : "api.themoviedb.org",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    req_data = req.json()
    return req_data
async def get_cookie() -> str:
    urlSearch = "https://raw.githubusercontent.com/quyendn/rapidclown/session/key.txt"
    req = await fetch(urlSearch, {
        "Referer": urlSearch,
        "Host": "raw.githubusercontent.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
    })
    req_data = req.text
    return req_data
async def get_streaming(dbid: str, s: int = None, e: int = None) -> dict :
    try:
        cookies = await get_cookie()
        json_array = json.loads(cookies)
        # Get a random element from the list
        random_element = random.choice(json_array)
        # Access the 'cookie' value from the selected random element
        random_cookie = random_element['cookie']
        #random_cookie = "session=eyJfZnJlc2giOmZhbHNlLCJwaG9uZV9udW1iZXIiOiJoYXN0YWcifQ.Zqm-xQ.tA6raijOmocPgyiQ3p6lCYI59cs"
        movie_info = await get_imdb_info(dbid)
        id = 0
        stream = []
        if movie_info['movie_results'] :
            id = movie_info['movie_results'][0]['id']
            #title = movie_info['movie_results'][0]['title']
            #release_date = movie_info['movie_results'][0]['release_date']
            #release_year = release_date.split('-')[0]
        if movie_info['tv_results'] :
            id = movie_info['tv_results'][0]['id']
            #title = movie_info['tv_results'][0]['title']
            #release_date = movie_info['tv_results'][0]['release_date']
            #release_year = release_date.split('-')[0]
        urlSearch = "https://susflix.tv/view/" + (f"tv" if s and e else 'movie') + f"/{id}"+ (f"/{s}/{e}" if s and e else '')
        #cookie = "session=eyJfZnJlc2giOmZhbHNlLCJwaG9uZV9udW1iZXIiOiJxdXllbmRuIn0.ZpjXHQ.n9nr8dv3o6SjduwDcMzQgIcHnd4"
        req = await fetch(urlSearch, {
            "Referer": f"https://susflix.tv/loading?id={id}",
            "Host": "susflix.tv",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Cookie": random_cookie,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        })
        req_data = req.text
        print(f"req_data : {req_data}")
        pattern = r"'Qualities':\s*\[(.*?)\]"
        match = re.search(pattern, req_data, re.DOTALL)
        if match:
            # Extract the Qualities array
            qualities_array = match.group(1)
            # Define the pattern to extract individual qualities
            quality_pattern = r"\{'path':\s*'(.*?)',\s*'quality':\s*'(.*?)'\}"
            # Find all matches
            qualities = re.findall(quality_pattern, qualities_array)
            #print(f"qualities : {qualities}")
            # Print the extracted qualities
            for path, quality in qualities:
                link_stream = ''.join(path).replace("\\\\", "")
                new_stream = {"path": link_stream, "quality": ''.join(quality)}
                if link_stream!= "":
                    stream.append(new_stream)
                #print(f"Path: {path}, Quality: {quality}")
        else:
            print("No match found")
        return {'result': stream}
     
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return {'result': []}