from Server import Server
import socket

SERVER_PORT = 8000
rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rtspSocket.bind(('', SERVER_PORT))
rtspSocket.listen(5)

# Receive client info (address,port) through RTSP/TCP session
while True:
    client = {}
    client['rtspSocket'] = rtspSocket.accept()
    server = Server(client)
    server.start()

