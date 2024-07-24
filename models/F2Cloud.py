from .utils import fetch
from typing import Union
import urllib.parse
from . import subtitle
import re
import base64
import json
from urllib.parse import quote, unquote
from base64 import b64encode, b64decode
def btoa(value: str) -> str:
    # btoa source: https://github.com/WebKit/WebKit/blob/fcd2b898ec08eb8b922ff1a60adda7436a9e71de/Source/JavaScriptCore/jsc.cpp#L1419
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
def enc(inp):
    inp = quote(inp)
    e = rc4('bZSQ97kGOREZeGik', inp)
    out = btoa(e)
    return out

def embed_enc(inp):
    inp = quote(inp)
    e = rc4('NeBk5CElH19ucfBU', inp)
    out = btoa(e)
    return out

def h_enc(inp):
    inp = quote(inp)
    e = rc4('Z7YMUOoLEjfNqPAt', inp)
    out = base64.b64encode(e.encode("latin-1")).decode().replace('/', '_').replace('+', '-')
    return out

def dec(inp):
    i = base64.b64decode(inp.replace('_', '/').replace('-', '+')).decode("latin-1")
    e = rc4('wnRQe3OZ1vMcD1ML', i)
    e = unquote(e)
    return e

def embed_dec(inp):
    i = base64.b64decode(inp.replace('_', '/').replace('-', '+')).decode("latin-1")
    e = rc4('eO74cTKZayUWH8x5', i)
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
    # DECODE SRC
    key_req        = await fetch('https://raw.githubusercontent.com/Ciarands/vidsrc-keys/main/keys.json')
    encrypt,decrypt      = key_req.json()
    print(f"encrypt:" + (encrypt))
    print(f"decrypt: "+ (decrypt))
    key1,key2      = key_req.json()

    #decoded_id     = await decode_data(key1, SRC_URL.split('/e/')[-1])
    #encoded_result = await decode_data(key2, decoded_id)
    #encoded_base64 = base64.b64encode(encoded_result)
    #key            = encoded_base64.decode('utf-8').replace('/', '_')
    url = urllib.parse.urlparse(url)
    embed_id = url.path.split("/")[2]
    h = h_enc(embed_id)
    print(f"h: {h}")
    mediainfo_url = f"https://vid2v11.site/mediainfo/{embed_enc(embed_id)}?{url.query}&ads=0&h={quote(h)}"
    print(f"mediainfo_url: {mediainfo_url}")
    # GET FUTOKEN
    #req = await fetch("https://vid2v11.site/futoken", {"Referer": url,"Host" : "vid2v11.site"})
    #fu_key = re.search(r"var\s+k\s*=\s*'([^']+)'", req.text).group(1)
    #data = f"{fu_key},{','.join([str(ord(fu_key[i % len(fu_key)]) + ord(key[i])) for i in range(len(key))])}"
    #data = f"{fu_key},{','.join([str(ord(fu_key[i % len(fu_key)]) + ord(key[i])) for i in range(len(key))])}"
    #print(f"[>] url https://vid2v11.site/mediainfo/{data}?{SUB_URL}&autostart=true")
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
