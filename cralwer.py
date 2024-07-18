import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import json
# Mock definitions for imports not provided
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

def login(user, password, ctx):
    url = f'{base_url}/login'
    data = {
        'user': user,
        'pass': password,
        'action': 'login'
    }
    response = requests.post(url, data=data)
    response_data = response.json()

    cookie_header = response.headers.get('Set-Cookie', '')
    if response_data.get('status') != 1:
        cookie_header = 'PHPSESSID=mk2p73c77qc28o5i5120843ruu;'

    cookies = parse_set_cookie(cookie_header)
    return cookies.get('PHPSESSID', '')

def parse_search(html_body):
    print(html_body)
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

# Constants
base_url = 'https://rips.cc'
username = '_sf_'
password = 'defonotscraping'

def combo_scraper(ctx):
    pass_cookie = login(username, password, ctx)
    
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
        'embeds': [],
        'stream': [
            {
                'id': 'primary',
                'type': 'file',
                'flags': ['CORS_ALLOWED'],
                'captions': captions,
                'qualities': {
                    720: {
                        'type': 'mp4',
                        'url': url,
                    },
                },
            },
        ],
    }

# Mock implementation of the make_sourcerer function
def make_sourcerer(config):
    return config

ee3_scraper = make_sourcerer({
    'id': 'ee3',
    'name': 'EE3',
    'rank': 111,
    'flags': ['CORS_ALLOWED'],
    'scrapeMovie': combo_scraper,
})
# Example usage
if __name__ == "__main__":
    media = {'title': 'Madame Web', 'year': 2024}
    ctx = MovieScrapeContext(media)
    output = combo_scraper(ctx)
    print(output)