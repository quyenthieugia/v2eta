import requests
import base64
import urllib.parse
import json
import re
from base64 import b64encode, b64decode
from urllib.parse import quote, unquote
def btoa(value: str) -> str:
    # btoa source: https://github.com/WebKit/WebKit/blob/fcd2b898ec08eb8b922ff1a60adda7436a9e71de/Source/JavaScriptCore/jsc.cpp#L1419
    binary = value.encode("latin-1")
    return b64encode(binary).decode()


def atob(value: str) -> str:
    binary = b64decode(value.encode())
    return binary.decode("latin-1")
def get_keys():
    url = "https://raw.githubusercontent.com/Ciarands/vidsrc-keys/main/keys.json"
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch decryption keys:", response.status_code)
        return None
    
    keys = response.json()
    return keys['encrypt'] + keys['decrypt']

keys = get_keys()

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
    e = rc4(keys[0], inp)
    out = btoa(e)
    return out

def embed_enc(inp):
    inp = quote(inp)
    e = rc4(keys[1], inp)
    out = btoa(e)
    return out

def h_enc(inp):
    inp = quote(inp)
    e = rc4(keys[2], inp)
    out = btoa(e)
    return out

def dec(inp):
    i = atob(inp)
    e = rc4(keys[3], i)
    e = unquote(e)
    return e

def embed_dec(inp):
    i = atob(inp)
    e = rc4(keys[4], i)
    e = unquote(e)
    return e

def get_subtitles(vidplay_link):
    if 'sub.info=' in vidplay_link:
        subtitle_link = vidplay_link.split('?sub.info=')[1].split('&')[0]
        subtitle_link = unquote(subtitle_link)
        subtitles_fetch = requests.get(subtitle_link).json()
        subtitles = [{'file': subtitle['file'], 'lang': subtitle['label']} for subtitle in subtitles_fetch]
        return subtitles
    return []

def episode(data_id):
    url = f"https://vidsrc.to/ajax/embed/episode/{data_id}/sources?token={quote(enc(data_id))}"
    print(f"url: {url}")
    resp = requests.get(url).json()
    f2cloud_id = resp['result'][0]['id']
    
    url = f"https://vidsrc.to/ajax/embed/source/{f2cloud_id}?token={urllib.parse.quote(enc(f2cloud_id))}"
    resp = requests.get(url).json()
    f2cloud_url = resp['result']['url']
    f2cloud_url_dec = dec(f2cloud_url)

    subtitles = get_subtitles(f2cloud_url_dec)
    
    url = urllib.parse.urlparse(f2cloud_url_dec)
    embed_id = url.path.split("/")[2]
    h = h_enc(embed_id)
    mediainfo_url = f"https://vid2v11.site/mediainfo/{embed_enc(embed_id)}{url.query}&ads=0&h={urllib.parse.quote(h)}"
    resp = requests.get(mediainfo_url).json()
    
    playlist = embed_dec(resp['result'])
    if isinstance(playlist, str):
        playlist = json.loads(playlist)
    
    source = playlist.get('sources', [{}])[0].get('file')

    data = {'file': source, 'sub': subtitles}
    return {'data': data}

def get_movie(id):
    resp = requests.get(f"https://vidsrc.to/embed/movie/{id}").text
    data_id = re.search(r'data-id="(.*?)"', resp).group(1)
    print(data_id)
    return episode(data_id)

def get_series(id, s, e):
    resp = requests.get(f"https://vidsrc.to/embed/tv/{id}/{s}/{e}").text
    data_id = re.search(r'data-id="(.*?)"', resp).group(1)
    return episode(data_id)

# Example usage
if __name__ == "__main__":
    #e = "?♀#ôyr»C:`"
    #out = base64.b64decode(e.encode()).decode().replace("/", "_").replace("+", '-')
    movie_data = get_movie('tt2975590')
    print(movie_data)

    #series_data = get_series('tt0944947', '1', '1')
    #print(series_data)