from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import json

# Constants
block_size = 16

# Helper Functions for Base64 Encoding and Decoding
def string_btoa(input_str):
    return base64.b64encode(input_str.encode('latin1')).decode('utf-8')

def string_atob(input_str):
    input_str = input_str + '=' * (-len(input_str) % 4)  # Add padding if necessary
    return base64.b64decode(input_str.encode('utf-8')).decode('latin1')
def derive_key_from_password(password, key_length=32):
    password_bytes = password.encode('latin1')
    if len(password_bytes) < key_length:
        # Pad or truncate the password to match the key length
        return password_bytes.ljust(key_length, b'\0')[:key_length]
    return password_bytes[:key_length]
# Custom JSON AES Encryption and Decryption
class CryptoJSAesJson:
    @staticmethod
    def encrypt(value, password):
        password_bytes = password.encode('utf-8')
        cipher = AES.new(password_bytes, AES.MODE_CBC)
        json_str = json.dumps(value)
        encrypted_bytes = cipher.encrypt(pad(json_str.encode('utf-8'), block_size))
        encrypted_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')
        iv_base64 = base64.b64encode(cipher.iv).decode('utf-8')
        return json.dumps({'ct': encrypted_base64, 'iv': iv_base64})

    @staticmethod
    def decrypt(json_str, password):
        print(f"password1:{password}")
        parsed_json = json.loads(json_str)
        print(f"parsed_json:{parsed_json}")
        encrypted_bytes = base64.b64decode(parsed_json['ct'])
        iv = base64.b64decode(parsed_json['iv'])
        new_pass = CryptoJSAesJson._generate_new_pass(parsed_json.get('m', ''), password)
        new_pass_bytes = new_pass.encode('latin1')
        print(f"new_pass_bytes:{new_pass_bytes}")
        print(f"iv:{iv}")
        cipher = AES.new(new_pass_bytes, AES.MODE_CBC, iv)
        
        print(f"cipher:{cipher}")
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), block_size)
        decrypted_json_str = decrypted_bytes.decode('utf-8')
        return json.loads(decrypted_json_str)

    @staticmethod
    def _generate_new_pass(m, password):
        print(f"password:{password}")
        r = password.split("\\x")
        print(f"r:{r}")
        new_pass = ""
        if m:
            reversed_m = string_atob(m[::-1])
            indices = reversed_m.split("|")
            print(f"indices:{indices}")
            for index in range(len(indices)):
                s = indices[index]
                idx = int(s) + 1
                new_pass += "\\x" + r[idx]
        print(f"new_pass:{new_pass}")
        return new_pass

# Example Usage
if __name__ == "__main__":
    # Example JSON data and password
    json_data = '{"ct":"RczM2jvgpA7xoPEHxIGUEdmhCC6MSfO7f8GrnxgqlVpDF6jXXl\/TM\/DrAfxdxSNfxAGMA1DQqAPvYJQA0dQ53HHLE5Lr2KaGLRafs1ZVdd0=","iv":"d6797b24dfd20cd9522025494153c21d","s":"f542a8014a58a5ac","m":"AOzwXNywnNxw3M8hTM8BTM8JTM8hDf5wnMzwXOywXMxwHM8dDf2wHMzwHN8RTM8FDf0MDfwIDfyQDfwQDf3IDfzMDf1EDf4IDfzEDfywHNywXOxw3NzwXOzwXN8ZjM8ZzM8NjM8JjM8FDN8VzM8FjM8NDN8dTM8FzM"}'
    secret_password = "\\x6c\\x44\\x30\\x4e\\x30\\x45\\x54\\x6c\\x4e\\x6d\\x4d\\x5a\\x57\\x4d\\x41\\x55\\x7a\\x44\\x31\\x57\\x69\\x30\\x52\\x6b\\x51\\x55\\x54\\x4f\\x6d\\x44\\x5a\\x4e\\x64\\x32\\x4f\\x59\\x4d\\x4d\\x3d\\x79\\x57\\x32\\x46\\x49"
    # Encrypt the JSON data with the password
    #encrypted_json = CryptoJSAesJson.encrypt(json_data, secret_password)
    #print('Encrypted JSON:', encrypted_json)

    # Decrypt the encrypted JSON with the password
    decrypted_json = CryptoJSAesJson.decrypt(json_data, secret_password)
    print('Decrypted JSON:', decrypted_json)
