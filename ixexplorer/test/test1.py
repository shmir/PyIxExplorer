import SimpleHTTPServer, SocketServer
httpd = SocketServer.TCPServer\
    (("", 161), SimpleHTTPServer.SimpleHTTPRequestHandler)
httpd.serve_forever()
