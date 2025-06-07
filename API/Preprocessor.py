from PIL import Image
from datetime import datetime
import logging
import json
from module import deepfakeDetector
import random
import base64
import io
import aiohttp
import asyncio
import requests
import sys

assumption = random.choice([0,1])
img_extensions = ['.jpg', '.jpeg', '.png', '.peng', '.bmp', '.gif', '.webp', '.svg', '.jpe', '.jfif', '.tar', '.tiff', '.tga']
vdo_extensions = ['.mp4','.mov', '.wmv', '.avi', '.avchd', '.flv', '.f4v', '.swf', '.mkv', '.webm', '.html5']
manifest = None
single_img_bin = []

def sum(a, b):
    return a+b

def sub(a, b):
    return a-b

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'assets', 'manifest.json')
with open(json_path, 'r') as data:
    manifest = json.load(data)
# module_dir = os.path.dirname(__file__)
# if os.path.exists(os.path.join(module_dir, 'module', 'temp.py')):
#     from module import temp as deepfakeDetector
# with open('./assets/manifest.json') as data:
#     manifest = json.load(data)

class Tools:
    def json_log(message):
        logging.basicConfig(filename='json_data.log',level=logging.DEBUG)
        logging.debug(json.dumps({"result": message}))

    def timeStamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def find_extension(media_data):
        header, _ = media_data.split(",", 1)
        ext = header.split(";")[0].split("/")[1].lower()
        return ext
    
    def is_image(image_data):
        valid_extensions = img_extensions
        if not image_data.startswith("data:image/"):
            return False
        try:
            header, encoded_data = image_data.split(",", 1)
            ext = header.split(";")[0].split("/")[1].lower()
            if ("."+ext) not in valid_extensions:
                return False
        except Exception as e:
            print(f"Error parsing image data URL: {e}")
            return False
        try:
            image_bytes = base64.b64decode(encoded_data)
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()  
            return True
        except Exception as e:
            print(f"Error to reading image: {e}")
            return False
    
    def is_video(video_data):
        valid_extensions = vdo_extensions
        if not video_data.startswith("data:video/"):
            return False
        try:
            header, encoded_data = video_data.split(",", 1)
            ext = header.split(";")[0].split("/")[1].lower()
            if ("."+ext) not in valid_extensions:
                return False
        except Exception as e:
            print(f"Error parsing image data URL: {e}")
            return False
        return True
    
    def base64_type(media_data):
        if not media_data.startswith("data:"):
            return False
        try:
            header, encoded_data = media_data.split(",", 1)
            type = header.split(":")[1].split("/")[0].lower()
            return type
        except Exception as e:
            print(f"Error to reading media: {e}")
            return False
        
    def base64_ext(media_data):
        if not media_data.startswith("data:"):
            return False
        try:
            header, encoded_data = media_data.split(",", 1)
            ext = header.split(";")[0].split("/")[1].lower()
            return ext
        except Exception as e:
            print(f"Error to reading media: {e}")
            return False
        
    def base64_size(base64_str):
        encoded = base64_str.split(",")[1] if "," in base64_str else base64_str
        size_bytes = len(encoded) * (3 / 4) - (encoded.endswith("==") * 2) - (encoded.endswith("=") * 1)
        return size_bytes / 1024
        
    def merge_list_to_string(array, delimiter=''):
        return delimiter.join(array)
    
    def represent(value):
        print(f"value: {str(value)}, Type: {type(value)}")

class MutableDict(dict):
    def update(self, key_path, new_value):
        key_list = key_path.split('.')
        current_dict = self
        # print(current_dict)
        if len(key_list) == 1:
            if key_list[0] not in current_dict:
                raise KeyError(f"Key '{key_list[0]}' not found in object")
            current_dict[key_list[0]] = new_value
            return self
        
        for key in key_list[:-1]:
            if key not in current_dict:
                raise KeyError(f"Key '{key}' not found in object")
            current_dict = current_dict[key]
            if not isinstance(current_dict, dict):
                raise ValueError(f"{key} is not a object")
            if key_list[-1] not in current_dict:
                raise KeyError(f"Key '{key_list[-1]}' not found in object")
            current_dict[key_list[-1]] = new_value
            return self
        
    def insert(self, key_path, value):
        key_list = key_path.split('.')
        current_dict = self
        if len(key_list) == 1:
            if key_list[0] in current_dict:
                print(f"\tInsert Key '{key_list[0]}' already exist")
            current_dict[key_list[0]] = value
            return self
        
        for key in key_list[:-1]:
            if key not in current_dict:
                current_dict[key] = {}
            current_dict = current_dict[key]
            if not isinstance(current_dict, dict):
                raise ValueError(f"{key} is not a object")
            if key_list[-1] in current_dict:
                print(f"\tInsert Key '{key_list[-1]}' already exist")
            current_dict[key_list[-1]] = value
            return self

class Responce:
    def model(key):
        type = Authentication.keyType(key)
        if type == False:
            return customException.accessException("/",key)
        if key == '' or key == None:
            key = 'Public Key'
        result = MutableDict(manifest['result_schema']).update("metadata.request_id", Responce.mask_key(key))
        result = result.update("metadata.timestamp", Tools.timeStamp())
        return result
    
    def mask_key(key: str) -> str:
        masked = []
        i = 0
        length = len(key)
        while i < length:
            if i < 6:
                masked.append(key[i])
            elif (i - 6) % 19 < 8:
                masked.append('*')
            else:
                masked.append(key[i])
            i += 1
        if length >= 3:
            masked[-3:] = key[-3:]
        return ''.join(masked)
    
    def initial_responce():
        schema = MutableDict(manifest['root_schema'])
        return schema['html_content']
    
    def compress_reponce(base64_str, max_size_kb=900, min_skip_size_kb=900):
        if Tools.is_image(base64_str) == False:
            return base64_str
        
        if Tools.base64_size(base64_str) <= min_skip_size_kb:
            return base64_str

        try:
            header, encoded = base64_str.split(",", 1)
            ext = header.split(";")[0].split("/")[-1].upper()

            image_data = base64.b64decode(encoded)
            image = Image.open(io.BytesIO(image_data))

            buffer = io.BytesIO()
            quality = 95

            while quality >= 10:
                buffer.seek(0)
                buffer.truncate(0)
                
                if ext in ["JPEG", "JPG", "JPE", "JFIF", "WEBP"]:
                    image = image.convert("RGB")

                if ext in ["JPEG", "JPG", "JPE", "JFIF", "WEBP", "TIFF"]:
                    image.save(buffer, format=ext, quality=quality, progressive=True)
                else:
                    image.save(buffer, format=ext, optimize=True)

                compressed_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                compressed_size_kb = Tools.base64_size(f"data:image/{ext.lower()};base64,{compressed_base64}")

                if compressed_size_kb <= max_size_kb:
                    return f"data:image/{ext.lower()};base64,{compressed_base64}"

                quality -= 5

            return f"data:image/{ext.lower()};base64,{compressed_base64}"

        except Exception as e:
            print(f"Error compressing image: {e}")
            return None


class Authentication:
    auth_file = './assets/auth.json'

    def isValidAccess(key):
        try:
            if key == '' or key == None:
                return True
            json_path = os.path.join(script_dir, 'assets', 'auth.json')
            with open(json_path, 'r') as data:
                auth_data = json.load(data)
                # with open(Authentication.auth_file) as data:
                #     auth_data = json.load(data)
                for i in range (0, len(auth_data['valid_key'])):
                    if key == auth_data['valid_key'][i]:
                        return True
                return True    # Invalid access / for your project
        except:
            return False
        
    def keyType(key):
        try:
            if key == '' or key == None:
                return 'Public'
            json_path = os.path.join(script_dir, 'assets', 'auth.json')
            with open(json_path, 'r') as data:
                auth_data = json.load(data)
                for i in range (0, len(auth_data['valid_key'])):
                    if key == auth_data['valid_key'][i]:
                        return 'Private'
                return False    # Fake key
        except:
            return False
        
    def userDetails(key):
        try:
            if key == '' or key == None:
                return 'Public user'
            json_path = os.path.join(script_dir, 'assets', 'auth.json')
            with open(json_path, 'r') as data:
                auth_data = json.load(data)
                for i in range (0, len(auth_data['valid_key'])):
                    if key == auth_data['valid_key'][i]:
                        try:
                            return MutableDict(auth_data['key_holder'][i]).insert("id", i)
                        except:
                            return "Non Reserved Private Key"
                return False
        except:
            return False

class customException:
    def error_schema():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, 'assets', 'manifest.json')
        with open(json_path, 'r') as data:
            manifest = json.load(data)
            return MutableDict(manifest['error_schema'])
    
    def methodException(path, method):
        error = (customException.error_schema()).update("error", "Method Exception")
        error = error.update("detail.desc", manifest['error_log'][20]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.method", method)
        error = error.update("status.code", 405)
        error = error.update("status.message", "Task Faild due to invaild method access")
        return error

    def notFoundException(path, method):
        error = (customException.error_schema()).update("error", "Path Exception")
        error = error.update("detail.desc", manifest['error_log'][20]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.method", method)
        error = error.update("status.code", 404)
        error = error.update("status.message", "Task Faild due to invaild hit point")
        return error

    def accessException(path, key):
        error = (customException.error_schema()).update("error", "Access Exception")
        error = error.update("detail.desc", manifest['error_log'][18]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.key", key)
        error = error.update("status.code", 401)
        error = error.update("status.message", "Task Faild due to unauthorized access")
        return error
    
    def unsupportException(path, extension):
        error = (customException.error_schema()).update("error", "Unsupport Media Exception")
        error = error.update("detail.desc", manifest['error_log'][1]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.extension", extension)
        error = error.update("network.url", "https://chsapi.vercel.app/api/")
        error = error.update("status.code", 415)
        error = error.update("status.message", "Task Faild due to invaild extension")
        return error
    
    def convertationException(path, extension):
        error = (customException.error_schema()).update("error", "Unsupport Convertation Exception")
        error = error.update("detail.desc", manifest['error_log'][17]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.extension", extension)
        error = error.update("network.url", "https://chsapi.vercel.app/api/")
        error = error.update("status.code", 422)
        error = error.update("status.message", "Task Faild due to unsupported convertation")
        return error
    
    def processException(path, data):
        error = (customException.error_schema()).update("error", "Unprocessable Exception")
        error = error.update("detail.desc", manifest['error_log'][19]['desc'])
        error = error.update("detail.path", path)
        error = error.insert("detail.input", data)
        error = error.update("network.url", "https://chsapi.vercel.app/api/")
        error = error.update("status.code", 422)
        error = error.update("status.message", "Task Faild due to unprocessable information")
        return error

class TaskMaster:
    def dfd_img(input_list, key, heatmap):
        key_type = Authentication.keyType(key)
        src = deepfakeDetector.detect_image(input_list, 'all', heatmap)
        return src
    def dfd_vdo(input_list, key, heatmap):
        src = deepfakeDetector.detect_video(input_list)
        return src

class Middleware:
    def security(method, allow_method, path, key):
        if not Authentication.isValidAccess(key):
            return customException.accessException(path, key)
        if method not in allow_method:
            return customException.methodException(path, method)
        
    async def substitution_decoder(cipher, key):
        key = key if key!='' else '1441'
        vocabulary = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@!*+#%$&^,|?/"
        plain_txt = ""

        key = (key * ((len(cipher) // len(key)) + 1))

        for i in range(len(cipher)):
            cipher_index = vocabulary.find(cipher[i])
            key_index = vocabulary.find(key[i])
            if cipher_index != -1 and key_index != -1:
                new_index = (cipher_index - key_index + len(vocabulary)) % len(vocabulary)
                plain_txt += vocabulary[new_index]
            else:
                plain_txt += cipher[i]

        return plain_txt

    
    async def substitution_encoder(plain_txt, key):
        key = key if key!='' else '1441'
        vocabulary = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@!*+#%$&^,|?/"
        cipher = ""
        key = key * (len(plain_txt) // len(key) + 1)
        key = key[:len(plain_txt)]
        for i in range(len(plain_txt)):
            plain_txt_index = vocabulary.find(plain_txt[i])
            key_index = vocabulary.find(key[i])
            if plain_txt_index != -1 and key_index != -1:
                new_index = (plain_txt_index + key_index) % len(vocabulary)
                cipher += vocabulary[new_index]
            else:
                cipher += plain_txt[i]
        return cipher
        