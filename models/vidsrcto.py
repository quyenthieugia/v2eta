import asyncio
import json
from bs4 import BeautifulSoup
from . import F2Cloud,filemoon
from .utils import fetch,error,decode_url
import base64
import re
from urllib.parse import quote, unquote
VIDSRC_KEY:str = "WXrUARXb1aDLaZjI"
SOURCES:list = ['F2Cloud','Filemoon']

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


def encode_to_url_safe_base64(s):
    # Chuyển đổi chuỗi thành bytes
    byte_str = s.encode('utf-8')
    
    # Mã hóa Base64
    encoded = base64.b64encode(byte_str).decode('utf-8')
    
    # Thay thế các ký tự không an toàn trong URL
    url_safe_encoded = re.sub(r'/', '_', encoded)
    url_safe_encoded = re.sub(r'\+', '-', url_safe_encoded)
    
    return url_safe_encoded

def enc(inp):
    print(f"[>] inp \"{inp}\"...")
    inp = quote(inp)
    print(f"encodeURIComponent {inp}")
    e = rc44('bZSQ97kGOREZeGik', inp)
    print(f"rc4:{e}")

    byte_string = e.encode()  # Đảm bảo sử dụng encoding UTF-8
    encoded = base64.b64encode(byte_string).decode()
    result = encoded.replace("/", "_").replace("+", "-")
    print(f"result {result}")

    out = base64.b64encode(e.encode()).decode().replace("/", "_").replace("+", '-')
    #out2 = base64.b64encode(e).decode().replace("/", "_").replace("+", '-')
    #test = encode_to_url_safe_base64(e)
    #print(f"[>] test \"{test}\"...")
    print(f"[>] out \"{out}\"...")
    #print(f"[>] out2 \"{out2}\"...")
    return out

def embed_enc(inp):
    inp = quote(inp)
    e = rc4('NeBk5CElH19ucfBU', inp)
    out = base64.b64encode(e.encode()).decode().replace("/", "_").replace("+", '-')
    return out

def h_enc(inp):
    inp = quote(inp)
    e = rc4('Z7YMUOoLEjfNqPAt', inp)
    out = base64.b64encode(e.encode()).decode().replace("/", "_").replace("+", '-')
    return out

def dec(inp):
    i = base64.b64decode(inp.replace("_", "/").replace("-", "+")).decode()
    e = rc4('wnRQe3OZ1vMcD1ML', i)
    e = unquote(e)
    return e

def embed_dec(inp):
    i = base64.b64decode(inp.replace("_", "/").replace("-", "+")).decode()
    e = rc4('eO74cTKZayUWH8x5', i)
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
    api_request:str = await fetch(f"https://vidsrc.to/ajax/embed/source/{source_id}",headers)
    if api_request.status_code == 200:
        try:
            data:dict = api_request.json()
            encrypted_source_url = data.get("result", {}).get("url")

            return {"decoded":await decode_url(encrypted_source_url,VIDSRC_KEY),"title":SOURCE_NAME}
        except:
            return {}
    else:
        return {}
        
async def get_stream(source_url:str,SOURCE_NAME:str):
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
    #key_req = await fetch('https://raw.githubusercontent.com/Ciarands/vidsrc-keys/main/keys.json')
    #data  = key_req.json()
    #encrypt = data.get("encrypt", [])
    #key1,key2,key3 = encrypt
    #print(key1)
    
    id_request = await fetch(id_url,headers)
    print(f"id_request: {id_request}")
    if id_request.status_code == 200:
        try:
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
