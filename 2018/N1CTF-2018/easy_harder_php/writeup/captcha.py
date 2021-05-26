# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# built-in imports
import random
import string
import multiprocessing
from hashlib import md5

CHARS = string.ascii_letters + string.digits


def work(cipher, stop_event):
    while not stop_event.is_set():
        s = ''.join(random.choice(CHARS) for _ in range(8))
        if md5(s.encode()).hexdigest()[:5] == cipher:
            print(f"\033[32m[+] {s}\033[0m")
            stop_event.set()


if __name__ == '__main__':
    cipher = input('captcha: ')
    processor_number = multiprocessing.cpu_count()
    stop_event = multiprocessing.Event()
    pool = multiprocessing.Pool(processes=processor_number)
    processes = [multiprocessing.Process(
        target=work, args=(cipher, stop_event)
    ) for _ in range(processor_number)]

    for p in processes:
        p.start()
    for p in processes:
        p.join()
