from Server import Server
import socket
import os
from preprocess import *

server_cache = 'server-cache'
movie_list = []
suffix = 'mp4'
files = os.listdir('.')

for item in files:
    s = item
    if s.split('.')[-1] == suffix:
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

SERVER_PORT = 8000
rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
rtspSocket.bind(('', SERVER_PORT))
rtspSocket.listen(5)

# Receive client info (address,port) through RTSP/TCP session
while True:
    client = {}
    client['rtspSocket'] = rtspSocket.accept()
    server = Server(SERVER_PORT,client)
    server.start()

