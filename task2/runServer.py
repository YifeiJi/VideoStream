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

_SERVER_PORT = 8000 #int(sys.argv[1])
_rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_rtspSocket.bind(('', _SERVER_PORT))
_rtspSocket.listen(5)

# Receive client info (address,port) through RTSP/TCP session
while True:

    con = _rtspSocket.accept()
    SERVER_PORT = randint(6000, 10000)
    reply = 'PORT ' + str(SERVER_PORT)
    reply = reply.encode('utf-8')
    print(reply)
    con[0].send(reply)

    rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtspSocket.bind(('', SERVER_PORT))
    rtspSocket.listen(5)
    client = {}
    client['rtspSocket'] = rtspSocket.accept()
    print('new client')
    server = Server(SERVER_PORT,client)
    server.start()
    print('stop')


