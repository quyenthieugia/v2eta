import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class CryptoJSAesJson:
    @staticmethod
    def decrypt(jsonStr, password):
        parseStr = json.loads(jsonStr)
        m = parseStr['m']
        newPass = ""
        r = password.split("\\x")
        
        m_reversed = ''.join(reversed(m))
        m_decoded = string_atob(m_reversed)
        indices = m_decoded.split("|")
        
        for s in indices:
            newPass += "\\x" + r[int(s) + 1]
        
        print("newPass: " + newPass)
        newPass_bytes = bytes.fromhex(newPass.replace("\\x", ""))
        
        ct = base64.b64decode(parseStr['ct'])
        iv = base64.b64decode(parseStr['iv'])
        s = base64.b64decode(parseStr['s'])
        
        cipher = AES.new(newPass_bytes, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ct), AES.block_size)
        
        return json.loads(decrypted.decode('utf-8'))

def string_btoa(input_str):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    output = ""
    i = 0
    block = 0
    
    while i < len(input_str) or (i % 1):
        if i < len(input_str):
            charCode = ord(input_str[i])
            if charCode > 0xff:
                raise ValueError("'btoa' failed: The string to be encoded contains characters outside of the Latin1 range.")
            block = (block << 8) | charCode
            i += 1
        
        output += chars[(block >> (6 * (3 - (i % 1)))) & 0x3F]
        block <<= 8
    
    while len(output) % 4:
        output += "="
    
    return output

def string_atob(input_str):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    str_cleaned = input_str.replace("=", "")
    output = ""
    buffer = 0
    bits = 0
    
    if len(str_cleaned) % 4 == 1:
        raise ValueError("'atob' failed: The string to be decoded is not correctly encoded.")
    
    for char in str_cleaned:
        buffer = (buffer << 6) | chars.index(char)
        bits += 6
        
        if bits >= 8:
            output += chr((buffer >> (bits - 8)) & 0xFF)
            bits -= 8
    
    return output

def Decrypt():
    hash = '{"ct":"JK528K00wAbR5IEwokEYn5mkwhzdU2t9Ce9wcS8muGVe2SvQ6IrlBWvMIeW7eb+dWkIwDUxz0LWwVNalDrSyPuwP9XSDWGjkSgAEIJ1fY8U=","iv":"1c31c003e02c449542b3b1e23d227401","s":"d9d3e8060f46ddd7","m":"wMzwHO8hjM8JjM8BjM8JDfxEDf1MDfzQDf0EDfyEDfwwXN8ZzM8NDf1IDf5w3NxwHNzwXOywHNyw3Myw3N8lTM8BDN8BTM8RDf4MDfxIDf4EDf3IDf2EDfyMDf1EDf2wXOzwXM0wHMzwXM8dzM8ZjM8JDN8NTM8FzM"}'
    secretKey = "\\x5a\\x44\\x52\\x7a\\x32\\x33\\x44\\x6a\\x4d\\x6c\\x55\\x57\\x54\\x44\\x45\\x52\\x4e\\x42\\x4e\\x4d\\x6d\\x6d\\x4f\\x56\\x6a\\x4e\\x6b\\x7a\\x57\\x4e\\x6c\\x4d\\x6a\\x3d\\x6a\\x4d\\x6b\\x5a\\x4e\\x4f\\x30\\x6c\\x4e\\x31"
    decode = CryptoJSAesJson.decrypt(hash, secretKey)
    return decode

# Example usage
if __name__ == "__main__":
    decrypted_data = Decrypt()
    print(decrypted_data)
