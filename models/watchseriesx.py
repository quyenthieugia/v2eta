import asyncio
import json
from bs4 import BeautifulSoup
from . import F2Cloud,filemoon
from .utils import fetch,error,decode_url
import base64
import re
from urllib.parse import quote, unquote
import requests
from base64 import b64encode, b64decode
from .utils import CouldntFetchKeys
from pymemcache.client import base
from pydantic import BaseModel
import logging
import bmemcached

HOST = "watchseriesx.to"
def btoa(value: str) -> str:
    binary = value.encode("latin-1")
    return b64encode(binary).decode()


def atob(value: str) -> str:
    binary = b64decode(value.encode())
    return binary.decode("latin-1")

def rc4(key, inp):
    e = [[]] * 9
    e[4] = list(range(256))
    e[3] = 0
    e[8] = ""
    i = 0
    for i in range(256):
        e[3] = (e[3] + e[4][i] + ord(key[i % len(key)])) % 256
        e[2] = e[4][i]
        e[4][i] = e[4][e[3]]
        e[4][e[3]] = e[2]
    
    i = 0
    e[3] = 0
    for j in range(len(inp)):
        i = (i + 1) % 256
        e[3] = (e[3] + e[4][i]) % 256
        e[2] = e[4][i]
        e[4][i] = e[4][e[3]]
        e[4][e[3]] = e[2]
        e[8] += chr(ord(inp[j]) ^ e[4][(e[4][i] + e[4][e[3]]) % 256])
    
    return e[8]
def enc(v_id: str) -> str:
    key = "VmSazcydpguRBnhG"
    v_id = quote(v_id)
    e = rc4(key, v_id)
    out = btoa(e)
    return out

def dec(inp):
    key = "8z5Ag5wgagfsOuhz"
    i = base64.b64decode(inp.replace('_', '/').replace('-', '+')).decode("latin-1")
    e = rc4(key, i)
    e = unquote(e)
    return e

async def tv(id, s=1, e=1):
        url = f"https://{HOST}/tv/{id}/{s}-{e}"
        resp = await fetch(url)
        data_id = re.search(r'data-id="(.*?)"', resp.text).group(1)
        print(f"data_id: {data_id}")
        url = f"https://{HOST}/ajax/episode/list/{data_id}?vrf={quote(enc(data_id))}"
        print(f"url: {url}")
        resp = await fetch(url)
        print(f"resp: {resp}")
        if resp.status_code == 200:
            try:
                data_text = json.dumps(resp.json()['result'])
                data_id = re.search(f'{s}-{e}" data-id="(.*?)"', resp.json()['result']).group(1)
                print(data_id)
                return await episode(data_id)
            except:
                return {}
async def movie(id):
        return await tv(id, 1, 1)
async def episode(data_id):
        print(f"episode data_id: {data_id}")
        url = f"https://{HOST}/ajax/server/list/{data_id}?vrf={quote(enc(data_id))}"
        print(f"episode url: {url}")
        resp = await fetch(url)
        if resp.status_code == 200:
            try:
                f2cloud = re.search(r'data-id="41" data-link-id="(.*?)"', resp.json()["result"]).group(1)
                print(f"f2cloud: {f2cloud}")
                url = f"https://{HOST}/ajax/server/{f2cloud}?vrf={quote(enc(f2cloud))}"
                print(f"f2cloud url: {url}")
                resp = await fetch(url)
                f2cloud_url_dec = dec(resp.json()["result"]["url"])
                print(f"f2cloud_url_dec: {f2cloud_url_dec}")
                data = await F2Cloud.handle(f2cloud_url_dec)
                return data
            except:
                return {}
           
async def get_imdb_info(imdb: str) -> str:
    api_url = "https://api.themoviedb.org/3/find/" + imdb + "?api_key=0f020a66f3e35379eef31c31363f2176&external_source=imdb_id"
    req = await fetch(api_url, {
        "Host" : "api.themoviedb.org",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    req_data = req.json()
    return req_data

async def search(query):
    url = f"https://{HOST}/filter?keyword={query}"
    resp = requests.get(url)
    print(resp)
    resp_text = resp.text
    print(resp_text)
    items = []
    regex = re.compile(r'<div class="item">([\s\S]*?)<\/div>\s*<\/div>')
    for match in regex.finditer(resp_text):
        items.append(match.group(1).strip())
    
    ret = []
    for item in items:
        regex_year = re.compile(r'<span>(\d{4}) - \d{1,3} min<\/span>')
        match_year = regex_year.search(item)
        year = match_year.group(1) if match_year else '0'
        
        regex_results = re.compile(r'<a href=".*?" class="title">.*?</a>')
        results = regex_results.findall(item)
        
        for r in results:
            regex_detail = re.compile(r'href="/(.*?)/(.*?)" .*>(.*?)</a>')
            match_detail = regex_detail.search(r)
            if match_detail:
                type, id, title = match_detail.groups()
                ret.append({'type': type, 'title': title, 'id': id, 'year': year})
    return ret

def compare_movie(media, title, year,type):
    return media['title'].lower() == title.lower() and media['type'].lower() == type.lower() and media['year'] == year
def compare_tv(media, title,type):
    return media['title'].lower() == title.lower() and media['type'].lower() == type.lower()
async def get_streaming(dbid: str, s: int = None, e: int = None) -> dict :
    try:
        media = 'tv' if s is not None and e is not None else "movie"
        movie_info = await get_imdb_info(dbid)
        id = 0
        title = ""
        release_year = 0
        if movie_info['movie_results'] :
            id = movie_info['movie_results'][0]['id']
            title = movie_info['movie_results'][0]['title']
            release_date = movie_info['movie_results'][0]['release_date']
            release_year = release_date.split('-')[0]
            print(release_year)
        if movie_info['tv_results'] :
            id = movie_info['tv_results'][0]['id']
            title = movie_info['tv_results'][0]['name']
            release_date = movie_info['tv_results'][0]['first_air_date']
            release_year = release_date.split('-')[0]
        search_movie = await search(title)
        print(search_movie)
        if media == "tv":
            id = next((item['id'] for item in search_movie if compare_tv(item, title,"tv")), None)
            movie_info = await tv(id,s,e)
            return movie_info
        else :
            id = next((item['id'] for item in search_movie if compare_movie(item, title,release_year,"movie")), None)
            movie_info = await movie(id)
            return movie_info
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return {'result': []}