from Server import Server
import socket

SERVER_PORT = 8000
rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rtspSocket.bind(('', SERVER_PORT))
rtspSocket.listen(5)

# Receive client info (address,port) through RTSP/TCP session
while True:
    _socket = rtspSocket.accept()
    server = Server(_socket)
    server.start()

