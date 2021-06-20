# openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
import ssl
from http.server import SimpleHTTPRequestHandler, HTTPServer

port = 8000
httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
print(f"Https Server Listening on [0.0.0.0:{port}]")
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./server.pem', server_side=True)
httpd.serve_forever()