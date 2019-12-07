from Server import Server
import socket
import sys
try:
    server_port = int(sys.argv[1])
except:
    print('Error')

rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rtsp_socket.bind(('', server_port))
rtsp_socket.listen(5)

while True:
    _socket = rtsp_socket.accept()
    server = Server(_socket)
    server.work()

