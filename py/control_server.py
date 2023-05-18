import os
import sys
import threading
import http
import mimetypes
import time

class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        for path, file in self.server.context.files:
            if path is None:
                path = file
            if self.path == '/' + path:
                with open(file, 'rb') as f:
                    data = f.read()
                content_type, encoding = mimetypes.guess_type(file, False)
                content_type = content_type or 'application/octet-stream'
                self.send_response(http.HTTPStatus.OK)
                self.send_header('Content-type', content_type)
                if encoding is not None:
                    self.send_header('Content-Encoding', encoding)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                break
        else:
            encoding = 'utf-8'
            self.send_response(http.HTTPStatus.NOT_FOUND)
            self.send_header("Content-type", "text/html")
            self.send_header('Content-Encoding', encoding)
            self.end_headers()
            self.wfile.write(bytes(f'''
<html>
    <head>
        <title>{self.server.context.user_args.get("title", "HTTPServer")}</title>
    </head>
    <body>
        <p>This is not the page You are looking for.</p>
        <p>"{self.path}"</p>
    </body>
</html>
                ''', encoding))
    
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        print(f'POST "{self.path}" [{length}] "{self.rfile.read(length)}"')
        self.send_response(http.HTTPStatus.NO_CONTENT)
        self.end_headers()

class _HTTPServerProxy(http.server.ThreadingHTTPServer):
    def __init__(self, context, server_address, RequestHandlerClass, bind_and_activate: bool = True) -> None:
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.context = context

class HTTPServer(object):
    def __init__(self, interface: str = 'localhost', port: int = 8080, poll_interval: float = 0.5, files = [], **kwargs) -> None:
        self.server_address = (interface, port)
        self._server_thread = None
        self._server_loop_poll_interval = poll_interval
        self.files = files
        self.user_args = kwargs
        if not mimetypes.inited:
            mimetypes.init()
    def run(self):
        if self._server_thread is not None and self._server_thread.is_alive():
            raise RuntimeError('Called run() on already running HTTP server.')
        self._server = _HTTPServerProxy(self, self.server_address, HTTPRequestHandler)
        self._server_thread = threading.Thread(target = self._server.serve_forever, args = (self._server_loop_poll_interval, ))
        self._server_thread.start()
    def stop(self):
        if self._server_thread is None or not self._server_thread.is_alive():
            return
        self._server.shutdown()
        self._server_thread.join()
        self._server_thread = None
        self._server.server_close()

def main(argv): # only for develepment purposes
    print(argv)
    hostName = "localhost"
    serverPort = 8080
    files = [('', os.path.join(os.path.split(argv[0])[0], 'control.html'))]
    server = HTTPServer(hostName, serverPort, files=files)
    server.run()
    print(f'Server started http://{server.server_address[0]}:{server.server_address[1]}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    server.stop()
    print('Server stopped.')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
