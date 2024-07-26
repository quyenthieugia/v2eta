import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import json
import logging
from .utils import fetch
from pydantic import BaseModel
from pymemcache.client import base
import bmemcached
# Constants
base_url = 'https://rips.cc'
username = '_sf_'
password = 'defonotscraping'
#memcache_client = base.Client(('localhost', 11211))
memcache_client = bmemcached.Client(('127.0.0.1:11211'),username='admin',password='Daodinh215186')
class Item(BaseModel):
    key: str
    value: str

class MovieScrapeContext:
    def __init__(self, media):
        self.media = media

    def proxied_fetcher(self, endpoint, options):
        url = f"{options['baseUrl']}{endpoint}"
        response = requests.post(url, data=options['body'], headers=options['headers'])
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
class NotFoundError(Exception):
    pass
class Caption:
    def __init__(self, id, url, type, has_cors_restrictions, language):
        self.id = id
        self.url = url
        self.type = type
        self.hasCorsRestrictions = has_cors_restrictions
        self.language = language

def set_value(item: Item):
    memcache_client.set(item.key, item.value)
    return {"message": "Value set successfully"}

def get_value(key: str):
    value = memcache_client.get(key)
    if value:
        return {"key": key, "value": value.decode('utf-8')}
    else:
        raise Exception('Key not found')
    
def compare_media(media, title, year):
    return media['title'].lower() == title.lower() and media['year'] == year

def make_cookie_header(cookies):
    return '; '.join([f'{key}={value}' for key, value in cookies.items()])

def parse_set_cookie(cookie_header):
    cookies = {}
    parts = cookie_header.split(';')
    for part in parts:
        if '=' in part:
            key, value = part.strip().split('=', 1)
            cookies[key] = value
    return cookies

def login(user, password):
    url = f'{base_url}/login'
    data = {
        'user': user,
        'pass': password,
        'action': 'login'
    }
    key_cache = f'COOKIE-{user}'
    cache_value = memcache_client.get(key_cache)
    if cache_value:
        value = cache_value.decode('utf-8')
        print(f'get cache value: {value}') 
        return value
    else:
        response = requests.post(url, data=data)
        response_data = response.json()
        cookie_header = response.headers.get('Set-Cookie', '')
        if response_data.get('status') != 1:
            cookie_header = 'PHPSESSID=mk2p73c77qc28o5i5120843ruu;'
        cookies = parse_set_cookie(cookie_header)
        cookies_value = cookies.get('PHPSESSID', '')
        print(f'set cache value: {cookies_value}') 
        memcache_client.set(key_cache, cookies_value,600)
        return cookies_value

def parse_search(html_body):
    results = []
    soup = BeautifulSoup(html_body, 'html.parser')
    divs = soup.find_all('div')
    for div in divs:
        title_element = div.find(class_='title')
        details_element = div.find(class_='details')
        control_buttons_element = div.find(class_='control-buttons')

        if title_element and details_element and control_buttons_element:
            title = title_element.get_text(strip=True)
            year = details_element.find('span').get_text(strip=True)
            id = control_buttons_element.get('data-id')

            if title and year and id:
                try:
                    year = int(year)
                    results.append({'title': title, 'year': year, 'id': id})
                except ValueError:
                    continue

    return results

def combo_scraper(ctx):
    pass_cookie = login(username, password)
    
    if not pass_cookie:
        raise Exception('Login failed')

    search_response = ctx.proxied_fetcher('/get', {
        'baseUrl': base_url,
        'method': 'POST',
        'body': {'query': ctx.media['title'], 'action': 'search'},
        'headers': {
            'cookie': make_cookie_header({'PHPSESSID': pass_cookie}),
        },
    })

    search_results = parse_search(search_response)
    id = next((item['id'] for item in search_results if compare_media(ctx.media, item['title'], item['year'])), None)
    if not id:
        raise NotFoundError('No watchable item found')

    details_response = ctx.proxied_fetcher('/get', {
        'baseUrl': base_url,
        'method': 'POST',
        'body': {'id': id, 'action': 'get_movie_info'},
        'headers': {
            'cookie': make_cookie_header({'PHPSESSID': pass_cookie}),
        },
    })
    
    details = json.loads(details_response)
    if not details['message']['video']:
        raise Exception('Failed to get the stream')
    key_response = ctx.proxied_fetcher('/renew', {
        'baseUrl': base_url,
        'method': 'POST',
        'body': {},
        'headers': {
            'cookie': make_cookie_header({'PHPSESSID': pass_cookie}),
        },
    })

    key_params = json.loads(key_response)
    if not key_params['k']:
        raise Exception('Failed to get the key')

    server = 'https://vid.ee3.me/vid/' if details['message']['server'] == '1' else 'https://vault.rips.cc/video/'
    k = key_params['k']
    url = f"{server}{details['message']['video']}?{urlencode({'k': k})}"
    captions = []

    if details['message']['subs'].lower() == 'yes' and details['message']['imdbID']:
        captions.append(Caption(
            id=f"https://rips.cc/subs/{details['message']['imdbID']}.vtt",
            url=f"https://rips.cc/subs/{details['message']['imdbID']}.vtt",
            type='vtt',
            has_cors_restrictions=False,
            language='en'
        ))

    return {
        'stream': [
            {
                'type': 'mp4',
                'url': url
            },
        ],
    }

def make_sourcerer(config):
    return config

ee3_scraper = make_sourcerer({
    'id': 'ee3',
    'name': 'EE3',
    'rank': 111,
    'flags': ['CORS_ALLOWED'],
    'scrapeMovie': combo_scraper,
})
async def get_imdb_info(imdb: str) -> str:
    api_url = "https://api.themoviedb.org/3/find/" + imdb + "?api_key=0f020a66f3e35379eef31c31363f2176&external_source=imdb_id"
    req = await fetch(api_url, {
        "Host" : "api.themoviedb.org",
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    req_data = req.json()
    return req_data
async def get_streaming(dbid: str, s: int = None, e: int = None) -> dict :
    try:
        movie_info = await get_imdb_info(dbid)
        print(movie_info)
        id = 0
        title = ""
        release_year = 0
        if movie_info['movie_results'] :
            id = movie_info['movie_results'][0]['id']
            title = movie_info['movie_results'][0]['title']
            release_date = movie_info['movie_results'][0]['release_date']
            release_year = release_date.split('-')[0]
        if movie_info['tv_results'] :
            id = movie_info['tv_results'][0]['id']
            title = movie_info['tv_results'][0]['title']
            release_date = movie_info['tv_results'][0]['release_date']
            release_year = release_date.split('-')[0]
        media = {'title': title, 'year': int(release_year)}
        ctx = MovieScrapeContext(media)
        output = combo_scraper(ctx)
        return output
    except Exception as e:
        logging.error(f"Error fetching server data: {e}")
        return {'result': []}