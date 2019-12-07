from Server import Server
import socket
import os
import sys
from random import *
from preprocess import *

server_cache = 'server-cache'
movie_list = []
suffix_list = ['avi', 'mp4']
files = os.listdir('.')

for item in files:
    s = item
    if s.split('.')[-1] in suffix_list:
        movie_list.append(item)

for item in movie_list:
    # print(item)
    file_path = os.path.join(server_cache, item)
    # print(file_path)
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        make_cache(item, file_path)

print("All Preprocess Done")
print('--------------------')

_server_port = int(sys.argv[1])
_rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_rtsp_socket.bind(('', _server_port))
_rtsp_socket.listen(5)

while True:

    con = _rtsp_socket.accept()
    while True:
        server_port = randint(20000,60000)
        try:
            if server_port == _server_port:
                continue
            rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            rtsp_socket.bind(('', server_port))

            break
        except:
            continue

    reply = 'PORT ' + str(server_port)
    reply = reply.encode('utf-8')
    #print(reply)
    con[0].send(reply)


    rtsp_socket.listen(5)
    rtsp_socket = rtsp_socket.accept()
    print('new client')
    server = Server(server_port,rtsp_socket)
    server.start()


