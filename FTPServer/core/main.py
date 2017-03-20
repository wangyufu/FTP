#!/usr/bin/env python
from core.ftp_server import FTPHandler
from conf import settings
import socketserver


def start():
    print('---going to start server----')
    server = socketserver.ThreadingTCPServer((settings.HOST, settings.PORT), FTPHandler)
    server.serve_forever()