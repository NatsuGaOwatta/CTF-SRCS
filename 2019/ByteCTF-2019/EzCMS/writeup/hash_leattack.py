# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: ptr-yudai

# built-in imports
import struct
from urllib.parse import quote


# MD5
def md5hex(message, iv=(0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476), prevlen=0):
    A, B, C, D = md5(message, iv, prevlen)
    md5sum = struct.pack('<I', A)
    md5sum += struct.pack('<I', B)
    md5sum += struct.pack('<I', C)
    md5sum += struct.pack('<I', D)
    return md5sum.hex()


def md5(message, iv=(0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476), prevlen=0):
    # パディングの付加
    padlen = 64 - ((len(message) + 8) % 64)
    msglen = (8 * (prevlen + len(message))) % 2**64
    if padlen < 64:
        message += b'\x80' + b'\x00' * (padlen - 1)
    # 長さの付加（リトルエンディアン
    message += struct.pack('<Q', msglen)
    # バッファの初期化
    A, B, C, D = iv
    # 補助関数の定義
    NOT = lambda X: X ^ 0xffffffff
    F = lambda X, Y, Z: (X & Y) | (NOT(X) & Z)
    G = lambda X, Y, Z: (X & Z) | (Y & NOT(Z))
    H = lambda X, Y, Z: X ^ Y ^ Z
    I = lambda X, Y, Z: Y ^ (X | NOT(Z))
    ROT_L = lambda x, n: (x << n) | (x >> (32 - n))
    OPE = lambda BOX, a, b, c, d, k, s, i: (b + (
        ROT_L(
            (a + BOX(b, c, d) + X[k] + T[i-1]) & 0xffffffff, s
        ) & 0xffffffff
    )) & 0xffffffff
    # 計算用数値配列の準備
    T = [
        0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee,
        0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501,
        0x698098d8, 0x8b44f7af, 0xffff5bb1, 0x895cd7be,
        0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821,
        0xf61e2562, 0xc040b340, 0x265e5a51, 0xe9b6c7aa,
        0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8,
        0x21e1cde6, 0xc33707d6, 0xf4d50d87, 0x455a14ed,
        0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a,
        0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
        0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70,
        0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05,
        0xd9d4d039, 0xe6db99e5, 0x1fa27cf8, 0xc4ac5665,
        0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039,
        0x655b59c3, 0x8f0ccc92, 0xffeff47d, 0x85845dd1,
        0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1,
        0xf7537e82, 0xbd3af235, 0x2ad7d2bb, 0xeb86d391
    ]
    # 算出処理
    for i in range(int(len(message) / 64)):
        M = message[i * 64:i * 64 + 64]
        X = []
        for j in range(16):
            X.append(struct.unpack('<I', M[j*4:j*4 + 4])[0])
        AA, BB, CC, DD = A, B, C, D
        # Round 1
        A = OPE(F, A, B, C, D, 0, 7, 1)
        D = OPE(F, D, A, B, C, 1, 12, 2)
        C = OPE(F, C, D, A, B, 2, 17, 3)
        B = OPE(F, B, C, D, A, 3, 22, 4)
        A = OPE(F, A, B, C, D, 4, 7, 5)
        D = OPE(F, D, A, B, C, 5, 12, 6)
        C = OPE(F, C, D, A, B, 6, 17, 7)
        B = OPE(F, B, C, D, A, 7, 22, 8)
        A = OPE(F, A, B, C, D, 8, 7, 9)
        D = OPE(F, D, A, B, C, 9, 12, 10)
        C = OPE(F, C, D, A, B, 10, 17, 11)
        B = OPE(F, B, C, D, A, 11, 22, 12)
        A = OPE(F, A, B, C, D, 12, 7, 13)
        D = OPE(F, D, A, B, C, 13, 12, 14)
        C = OPE(F, C, D, A, B, 14, 17, 15)
        B = OPE(F, B, C, D, A, 15, 22, 16)
        # Round 2
        A = OPE(G, A, B, C, D, 1, 5, 17)
        D = OPE(G, D, A, B, C, 6, 9, 18)
        C = OPE(G, C, D, A, B, 11, 14, 19)
        B = OPE(G, B, C, D, A, 0, 20, 20)
        A = OPE(G, A, B, C, D, 5, 5, 21)
        D = OPE(G, D, A, B, C, 10, 9, 22)
        C = OPE(G, C, D, A, B, 15, 14, 23)
        B = OPE(G, B, C, D, A, 4, 20, 24)
        A = OPE(G, A, B, C, D, 9, 5, 25)
        D = OPE(G, D, A, B, C, 14, 9, 26)
        C = OPE(G, C, D, A, B, 3, 14, 27)
        B = OPE(G, B, C, D, A, 8, 20, 28)
        A = OPE(G, A, B, C, D, 13, 5, 29)
        D = OPE(G, D, A, B, C, 2, 9, 30)
        C = OPE(G, C, D, A, B, 7, 14, 31)
        B = OPE(G, B, C, D, A, 12, 20, 32)
        # Round 3
        A = OPE(H, A, B, C, D, 5, 4, 33)
        D = OPE(H, D, A, B, C, 8, 11, 34)
        C = OPE(H, C, D, A, B, 11, 16, 35)
        B = OPE(H, B, C, D, A, 14, 23, 36)
        A = OPE(H, A, B, C, D, 1, 4, 37)
        D = OPE(H, D, A, B, C, 4, 11, 38)
        C = OPE(H, C, D, A, B, 7, 16, 39)
        B = OPE(H, B, C, D, A, 10, 23, 40)
        A = OPE(H, A, B, C, D, 13, 4, 41)
        D = OPE(H, D, A, B, C, 0, 11, 42)
        C = OPE(H, C, D, A, B, 3, 16, 43)
        B = OPE(H, B, C, D, A, 6, 23, 44)
        A = OPE(H, A, B, C, D, 9, 4, 45)
        D = OPE(H, D, A, B, C, 12, 11, 46)
        C = OPE(H, C, D, A, B, 15, 16, 47)
        B = OPE(H, B, C, D, A, 2, 23, 48)
        # Round 4
        A = OPE(I, A, B, C, D, 0, 6, 49)
        D = OPE(I, D, A, B, C, 7, 10, 50)
        C = OPE(I, C, D, A, B, 14, 15, 51)
        B = OPE(I, B, C, D, A, 5, 21, 52)
        A = OPE(I, A, B, C, D, 12, 6, 53)
        D = OPE(I, D, A, B, C, 3, 10, 54)
        C = OPE(I, C, D, A, B, 10, 15, 55)
        B = OPE(I, B, C, D, A, 1, 21, 56)
        A = OPE(I, A, B, C, D, 8, 6, 57)
        D = OPE(I, D, A, B, C, 15, 10, 58)
        C = OPE(I, C, D, A, B, 6, 15, 59)
        B = OPE(I, B, C, D, A, 13, 21, 60)
        A = OPE(I, A, B, C, D, 4, 6, 61)
        D = OPE(I, D, A, B, C, 11, 10, 62)
        C = OPE(I, C, D, A, B, 2, 15, 63)
        B = OPE(I, B, C, D, A, 9, 21, 64)
        # 加算
        A = (A + AA) % 2**32
        B = (B + BB) % 2**32
        C = (C + CC) % 2**32
        D = (D + DD) % 2**32
    # 出力
    return (A, B, C, D)


# Length Extension Attack
def leattack(length, md5h, m1, m2):
    if len(md5h) != 32:
        raise ValueError("Invalid MD5 Length")
    md5 = bytes.fromhex(md5h)
    # 出力状態の取得
    A = struct.unpack('<I', md5[0:4])[0]
    B = struct.unpack('<I', md5[4:8])[0]
    C = struct.unpack('<I', md5[8:12])[0]
    D = struct.unpack('<I', md5[12:16])[0]
    # パディングの付加
    data = b'?' * length + m1.encode()
    padlen = 64 - ((len(data) + 8) % 64)
    msglen = (8 * len(data)) % 2**64
    if padlen < 64:
        data += b'\x80' + b'\x00' * (padlen - 1)
    # 長さの付加（リトルエンディアン）
    data += struct.pack('<Q', msglen)
    # 追加バイト付加
    result = md5hex(m2.encode(), iv=(A, B, C, D), prevlen=len(data))
    data += m2.encode()
    return result, data[length:]


if __name__ == '__main__':
    # SALT = "hoge"
    # md5(SALT+m1)からmd5(SALT+m1+???+m2)を計算
    # m1 = "user"
    # known_md5 = md5hex(SALT + m1)
    # m2 = "|priv:teacher"
    known_md5 = input("Input Signature: ")
    pre = input("Input Data: ")
    length = int(input("Input Key Length: "))
    post = input("Input Data to Add: ")
    new_md5, data = leattack(length, known_md5, pre, post)
    print(f"known_md5 = {known_md5}")
    print(f"\033[01;32mnew_md5   = {new_md5}\033[0m")
    print(f"data      = {quote(data)}")
