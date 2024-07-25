import httpx,base64
from fastapi import HTTPException
from urllib.parse import unquote
from typing import Union
BASE = 'http://localhost:8000'

async def default():
    return ''

async def error(err:str):
    # TODO
    #    return {
    #        "status":500,
    #        "info":err,
    #        "sources":[]
    #    }
    print(err) # for understanding whats gone wrong in the deployment.viewable in vercel logs.
    return {}
async def decode_url(encrypted_source_url:str,VIDSRC_KEY:str):
    standardized_input = encrypted_source_url.replace('_', '/').replace('-', '+')
    binary_data = base64.b64decode(standardized_input)
    encoded = bytearray(binary_data)
    key_bytes = bytes(VIDSRC_KEY, 'utf-8')
    j = 0
    s = bytearray(range(256))

    for i in range(256):
      j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
      s[i], s[j] = s[j], s[i]

    decoded = bytearray(len(encoded))
    i = 0
    k = 0
    for index in range(len(encoded)):
      i = (i + 1) & 0xff
      k = (k + s[i]) & 0xff
      s[i], s[k] = s[k], s[i]
      t = (s[i] + s[k]) & 0xff
      decoded[index] = encoded[index] ^ s[t]
    decoded_text = decoded.decode('utf-8')
    return unquote(decoded_text)

async def fetch(url:str,headers:dict={},method:str="GET",data=None,redirects:bool=True):
    async with httpx.AsyncClient(follow_redirects=redirects) as client:
        if method=="GET":
            response = await client.get(url,headers=headers)
            return response
        if method=="POST":
            response = await client.post(url,headers=headers,data=data)
            return response
        else:
            return "ERROR"
@staticmethod
def decode_data(key: str, data: Union[bytearray, str]) -> bytearray:
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
            raise RC4DecodeError("Unsupported data type in the input")

    return decoded
@staticmethod
def int_2_base(x: int, base: int) -> str:
    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"

    if x < 0:
        sign = -1
    elif x == 0:
        return 0
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(charset[int(x % base)])
        x = int(x / base)
    
    if sign < 0:
        digits.append('-')
    digits.reverse()

    return ''.join(digits)

@staticmethod
def decode_base64_url_safe(s: str) -> bytearray:
    standardized_input = s.replace('_', '/').replace('-', '+')
    binary_data = base64.b64decode(standardized_input)
    return bytearray(binary_data)        
# Errors
class VidSrcError(Exception):
    '''Base Error'''
    pass

class CouldntFetchKeys(VidSrcError):
    '''Failed to fetch decryption keys for vidplay'''
    pass

class RC4DecodeError(VidSrcError):
    '''Failed to decode RC4 data (current design choices == only ever ValueError)'''
    pass

class NoSourcesFound(VidSrcError):
    '''Failed to find any media sources @ the provided source'''
    pass