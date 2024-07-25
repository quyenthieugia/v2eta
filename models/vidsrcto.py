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
VIDSRC_KEY:str = "WXrUARXb1aDLaZjI"
SOURCES:list = ['F2Cloud','Filemoon']

memcache_server = '127.0.0.1'
memcache_port = 11211
memcache_username = 'admin'
memcache_password = 'Daodinh215186'
#memcache_client = base.Client((memcache_server, memcache_port),username = memcache_username,password = memcache_password)
#memcache_client = bmemcached.Client(('157.245.131.248', 11211), username='admin', password='Daodinh215186')
memcache_client = bmemcached.Client(('127.0.0.1:11211'),username='admin',password='Daodinh215186')
#memcache_client = base.Client(('localhost', 11211))
#memcache_client.

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

def rc44(key, inp):
    S = list(range(256))
    j = 0
    key_length = len(key)
    
    # Key Scheduling Algorithm (KSA)
    for i in range(256):
        j = (j + S[i] + ord(key[i % key_length])) % 256
        S[i], S[j] = S[j], S[i]

    # Pseudo-Random Generation Algorithm (PRGA)
    i = 0
    j = 0
    output = []

    for char in inp:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        output.append(chr(ord(char) ^ K))
    
    return ''.join(output)

class Item(BaseModel):
    key: str
    value: str
def set_value(item: Item):
    memcache_client.set(item.key, item.value)
    return {"message": "Value set successfully"}

def get_value(key: str):
    value = memcache_client.get(key)
    if value:
        return {"key": key, "value": value.decode('utf-8')}
    else:
        raise Exception('Key not found')
@staticmethod
def get_key(enc: bool, num: int) -> str:
    try:
        key_cache = "KEY-CACHE-VIDSRC"
        cache_value = memcache_client.get(key_cache)
        if cache_value:
            #keys = cache_value.decode('utf-8')
            data_dict = json.loads(cache_value)
            print(f"cache value: {data_dict}")
            return data_dict["encrypt" if enc else "decrypt"][num]
        else:
            req = requests.get('https://raw.githubusercontent.com/Ciarands/vidsrc-keys/main/keys.json')
            if req.status_code != 200:
                raise CouldntFetchKeys("Failed to fetch decryption keys!")
            keys = req.json()
            json_data = json.dumps(keys)
            memcache_client.set(key_cache, json_data,60)
            return keys["encrypt" if enc else "decrypt"][num]
    except Exception as e:
        logging.error(f"Error fetching keys: {e}")
        return ""

def get_decryption_key() -> str:
    return get_key(False, 0)

def get_embed_decryption_key() -> str:
    return get_key(False, 1)

def get_encryption_key() -> str:
    return get_key(True, 0)

def get_embed_encryption_key() -> str:
    key_embed = get_key(True, 1)
    return get_key(True, 1)

def get_h_encryption_key() -> str:
    return get_key(True, 2)


def encode_to_url_safe_base64(s):
    # Chuyển đổi chuỗi thành bytes
    byte_str = s.encode('utf-8')
    
    # Mã hóa Base64
    encoded = base64.b64encode(byte_str).decode('utf-8')
    
    # Thay thế các ký tự không an toàn trong URL
    url_safe_encoded = re.sub(r'/', '_', encoded)
    url_safe_encoded = re.sub(r'\+', '-', url_safe_encoded)
    
    return url_safe_encoded

def enc(v_id: str) -> str:
    key = get_encryption_key()
    v_id = quote(v_id)
    e = rc4(key, v_id)
    out = btoa(e)
    return out

def embed_enc(inp):
    key = get_embed_encryption_key()
    inp = quote(inp)
    e = rc4(key, inp)
    out = btoa(e)
    return out

def h_enc(inp):
    inp = quote(inp)
    key = get_h_encryption_key()
    print(f"h_enc: {key}")
    e = rc4(key, inp)
    out = base64.b64encode(e.encode("latin-1")).decode().replace('/', '_').replace('+', '-')
    return out

def dec(inp):
    key = get_decryption_key()
    i = base64.b64decode(inp.replace('_', '/').replace('-', '+')).decode("latin-1")
    e = rc4(key, i)
    e = unquote(e)
    return e

def embed_dec(inp):
    key = get_embed_decryption_key()
    i = base64.b64decode(inp.replace('_', '/').replace('-', '+')).decode("latin-1")
    e = rc4(key, i)
    e = unquote(e)
    return e

async def get_source(source_id:str,SOURCE_NAME:str) -> str:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-GB,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Brave\";v=\"122\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1"
    }
    token = quote(enc(source_id))
    api_request:str = await fetch(f"https://vidsrc.to/ajax/embed/source/{source_id}?token={token}",headers)
    if api_request.status_code == 200:
        try:
            data:dict = api_request.json()
            encrypted_source_url = data.get("result", {}).get("url")
            decrypted_source_url = dec(encrypted_source_url)
            print(f"decrypted_source_url: {decrypted_source_url}")
            return {"decoded":decrypted_source_url,"title":SOURCE_NAME}
        except:
            return {}
    else:
        return {}
        
async def get_stream(source_url:str,SOURCE_NAME:str):
    print(f"source_url: {source_url}")
   
    RESULT = {}
    RESULT['name'] = SOURCE_NAME
    if SOURCE_NAME==SOURCES[0]:
        RESULT['data'] = await F2Cloud.handle(source_url)
        return RESULT
    # elif SOURCE_NAME==SOURCES[1]:
    #     RESULT['data'] = await filemoon.handle(source_url)
    #     return RESULT
    else:
        return {"name":SOURCE_NAME,"source":'',"subtitle":[]}
async def get_futoken(source_url:str):
    RESULT = {}
    RESULT['data'] = await F2Cloud.handle_futoken(source_url)
    return RESULT
    
async def get(dbid:str,s:int=None,e:int=None):
    media = 'tv' if s is not None and e is not None else "movie"
    id_url = f"https://vidsrc.to/embed/{media}/{dbid}" + (f"/{s}/{e}" if s and e else '')
    print(f"[>] id_url \"{id_url}\"...")
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-GB,en;q=0.9",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Brave\";v=\"122\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1"
    }
   
    id_request = await fetch(id_url,headers)
    req = requests.get(id_url)
    print(f"request: {id_request}")
    print(f"text: {req}")
    if id_request.status_code == 200:
        try:
            print(f"text: {id_request.text}")
            soup = BeautifulSoup(id_request.text, "html.parser")
            sources_code = soup.find('a', {'data-id': True}).get("data-id",None)
            if sources_code == None:
                return await error("media unavailable.")
            else:
                token = quote(enc(sources_code))
                print(f"token: {token}")
                url_source = f"https://vidsrc.to/ajax/embed/episode/{sources_code}/sources?token={token}"
                print(f"url_source {url_source}")
                source_id_request = await fetch(f"https://vidsrc.to/ajax/embed/episode/{sources_code}/sources?token={token}",headers)
                print(f"source_id_request: {source_id_request}")
                source_id = source_id_request.json()['result']
                SOURCE_RESULTS = []
                for source in source_id:
                    if source.get('title') in SOURCES:
                        SOURCE_RESULTS.append({'id':source.get('id'),'title':source.get('title')})

                SOURCE_URLS = await asyncio.gather(
                    *[get_source(R.get('id'),R.get('title')) for R in SOURCE_RESULTS]
                )
                SOURCE_STREAMS = await asyncio.gather(
                    *[get_stream(R.get('decoded'),R.get('title')) for R in SOURCE_URLS]
                )
                return SOURCE_STREAMS
        except:
            return await error("backend id not working.")
    else:
        return await error(f"backend not working.[{id_request.status_code}]")
