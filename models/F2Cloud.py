from .utils import fetch
from typing import Union
import urllib.parse
from . import subtitle
import re
import base64
import json
from urllib.parse import quote, unquote
from base64 import b64encode, b64decode
import requests
from .utils import CouldntFetchKeys
from pymemcache.client import base
import bmemcached
from pydantic import BaseModel
import logging
#memcache_client = base.Client(('localhost', 11211))
memcache_client = bmemcached.Client(('127.0.0.1:11211'),username='admin',password='Daodinh215186')
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
def get_key(enc: bool, num: int) -> str:
    try:
        key_cache = "KEY-CACHE-VIDSRC"
        cache_value = memcache_client.get(key_cache)
        if cache_value:
            #keys = cache_value.decode('utf-8')
            data_dict = json.loads(cache_value)
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

async def decode_data(key: str, data: Union[bytearray, str]) -> bytearray:
    key_bytes = bytes(key, 'utf-8')
    s = bytearray(range(256))
    j = 0

    for i in range(256):
        j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
        s[i], s[j] = s[j], s[i]

    decoded = bytearray(len(data))
    i = 0
    k = 0

    for index in range(len(data)):
        i = (i + 1) & 0xff
        k = (k + s[i]) & 0xff
        s[i], s[k] = s[k], s[i]
        t = (s[i] + s[k]) & 0xff

        if isinstance(data[index], str):
            decoded[index] = ord(data[index]) ^ s[t]
        elif isinstance(data[index], int):
            decoded[index] = data[index] ^ s[t]
        else:
            return None

    return decoded
async def handle(url) -> dict:
    URL = url.split("?")
    SRC_URL = URL[0]
    SUB_URL = URL[1]
    # GET SUB
    subtitles = {}
    subtitles = await subtitle.vscsubs(SUB_URL)
    url = urllib.parse.urlparse(url)
    embed_id = url.path.split("/")[2]
    h = h_enc(embed_id)
    print(f"h: {h}")
    mediainfo_url = f"https://vid2v11.site/mediainfo/{embed_enc(embed_id)}?{url.query}&ads=0&h={quote(h)}"
    print(f"mediainfo_url: {mediainfo_url}")
    # GET SRC
    req = await fetch(mediainfo_url)
    req_data = req.json()
    playlist = embed_dec(req_data.get("result"))
    print(f"[>] result \"{playlist}\"...")
    if isinstance(playlist, str):
        playlist = json.loads(playlist)
    # RETURN IT
    if type(playlist) == dict:
        print("dict")
        return {
            'stream':playlist.get("sources", [{}])[0].get("file"),
            'subtitle':subtitles
        }
    else:
        print(playlist.get("sources", [{}])[0].get("file"))
        return {
            'stream':playlist.get("sources", [{}])[0].get("file"),
            'subtitle':subtitles
        }
async def handle_futoken(imdb_id) -> dict:
    # GET FUTOKEN
    req = await fetch("https://embed.smashystream.com/dataaa.php?imdb="+imdb_id, {
        "Referer": "https://player.smashy.stream/",
        "Host" : "embed.smashystream.com",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Sec-Fetch-Site" : "cross-site"
    })
    req_data = req.json()
    if type(req_data.get("url_array")) == dict:
        return {
            'url_array':req_data.get("url_array")
        }
    else:
        return {}
