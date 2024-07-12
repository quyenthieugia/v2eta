from .utils import fetch
from typing import Union
from . import subtitle
import re
import base64
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
    key_req        = await fetch('https://raw.githubusercontent.com/quyendn/rapidclown/vidplay/key.json')
    key1,key2      = key_req.json()
    decoded_id     = await decode_data(key1, SRC_URL.split('/e/')[-1])
    encoded_result = await decode_data(key2, decoded_id)
    encoded_base64 = base64.b64encode(encoded_result)
    key            = encoded_base64.decode('utf-8').replace('/', '_')

    # GET FUTOKEN
<<<<<<< HEAD
    req = await fetch("https://vid2v11.site/futoken", {"Referer": url})
   
    fu_key = re.search(r"var\s+k\s*=\s*'([^']+)'", req.text).group(1)
=======
    req = await fetch("https://vid2v11.site/futoken", {"Referer": url,"Host" : "vid2v11.site"})
    fu_key = re.search(r"var\s+k\s*=\s*'([^']+)'", req.text).group(1)
    print(f"[>] fu_key \"{fu_key}\"...")
    data = f"{fu_key},{','.join([str(ord(fu_key[i % len(fu_key)]) + ord(key[i])) for i in range(len(key))])}"
>>>>>>> 059f59955586259c5ff435d798c8482dd6c4e29c
    
    print(f"[>] fu_key {fu_key}...")
    data = f"{fu_key},{','.join([str(ord(fu_key[i % len(fu_key)]) + ord(key[i])) for i in range(len(key))])}"
    print(f"[>] url https://vid2v11.site/mediainfo/{data}?{SUB_URL}&autostart=true")
    # GET SRC
    req = await fetch(f"https://vid2v11.site/mediainfo/{data}?{SUB_URL}&autostart=true",headers={"Referer": url})
    req_data = req.json()
<<<<<<< HEAD
    print(f"[>] req_data {req_data}...")
=======
    print(f"[>] req_data \"{req_data}\"...")
>>>>>>> 059f59955586259c5ff435d798c8482dd6c4e29c
    # RETURN IT
    if type(req_data.get("result")) == dict:
        return {
            'stream':req_data.get("result").get("sources", [{}])[0].get("file"),
            'subtitle':subtitles
        }
    else:
        return {
            'stream':req_data.get("result").get("sources", [{}])[0].get("file"),
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
