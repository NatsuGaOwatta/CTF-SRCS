<?php
ob_start();
include('config.php');
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>EzCMS</title>
</head>

<body>
<h2>Login platform</h2>
<div>
    <p>假装这是一个超级漂亮的前端</p>
    <p>先来登录吧~</p>
</div>
<form action="index.php" method="post" enctype="multipart/form-data">
    <label for="file">用户名：</label>
    <input type="text" name="username" id="username"><br>
    <label for="file">密码：</label>
    <input type="password" name="password" id="password"><br>
    <input type="submit" name="login" value="提交">
</form>
</body>
</html>

<?php
error_reporting(0);
if (isset($_POST['username']) && isset($_POST['password'])){
    $username = $_POST['username'];
    $password = $_POST['password'];
    $username = urldecode($username);
    $password = urldecode($password);
    if ($password === "admin"){
        die("u r not admin !!!");
    }

    $_SESSION['username'] = $username;
    $_SESSION['password'] = $password;

    if (login()){
        echo '<script>location.href="upload.php";</script>';
    }
}

ob_end_flush();
?>
