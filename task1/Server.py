import socket
from random import *
import threading
from RtpPacket import *
import os
class Server:
    def __init__(self, rtspSocket):
        self.rtspSocket = rtspSocket
        self.rtpSocket = None
        self.status = 'NOT READY'
        self.filename = None
        self.base_path = './picture'
        self.picture_list = []
        self.picture_num = 0
        self.frame_number = 0
        self.event = None

    def start(self):
        self.make_picture_list()
        threading.Thread(target=self.listen_rtsp).start()

    def make_picture_list(self):
        files = os.listdir(self.base_path)

        for item in files:
            if '.jpg' in item:
                self.picture_list.append(item)
        self.picture_num = len(self.picture_list)

    def listen_rtsp(self):
        conn = self.rtspSocket[0]
        while True:
            res = conn.recv(256)
            if res:
                print ("Received:\n")
                print(res)
                self.handleRtsp(res)

    def handleRtsp(self,request):
        request = request.decode('utf-8')
        request = request.split('\n')
        print('request:',request)
        first_item = request[0].split(' ')

        cmd = first_item[0]
        print('cmd:',cmd)

        filename = first_item[1]
        print('filename:',filename)

        seq = request[1].split(' ')[1]
        print('seq:', seq)

        if cmd == 'SETUP':

            if self.status == 'NOT READY':
                # Update state
                print ("SETUP ing")
                try:
                    self.filename = filename
                    self.status = 'READY'
                except:
                    self.reply_rtsp('FILE_NOT_FOUND_404', seq)

                # Generate a randomized RTSP session ID
                self.session = randint(100000, 999999)
                self.frame_number = 0
                self.reply_rtsp('OK_200', seq)
                self.rtpPort = request[2].split(' ')[3]
            else:
                pass

        elif cmd == 'TEARDOWN':
            self.event.set()
            self.reply_rtsp('OK_200', seq)
            self.rtpSocket.close()

        elif cmd == 'PLAY':
            self.status = 'PLAYING'
            self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.event = threading.Event()
            self.reply_rtsp('OK_200', seq)
            threading.Thread(target=self.listen_rtsp).start()
            self.send_rtp()



        elif cmd == 'PAUSE':
            print('pause')
            print(self.status)
            if self.status == 'PLAYING':
                self.status = 'READY'
                self.event.set()
                self.reply_rtsp('OK_200', seq)
        else:
            pass

    def reply_rtsp(self, code, seq):
        if code == 'OK_200':

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.session)
            print('reply')
            print(reply)
            reply = reply.encode('utf-8')
            connSocket = self.rtspSocket[0]
            connSocket.send(reply)

        elif code == 'FILE_NOT_FOUND_404':
            print ("404 NOT FOUND")
        elif code == 'CON_ERR_500':
            print ("500 CONNECTION ERROR")

    def send_rtp(self):
        #print('send Rtp ready')
        while True:
            self.event.wait(0.01)
            if self.event.isSet():
                break
            filename = self.picture_list[self.frame_number]
            #str(frameNumber) + '.jpg'
            print(filename)
            filepath = os.path.join(self.base_path,filename)
            f = open(filepath,'rb')
            data = f.read()
            if data:
                try:
                    address = self.rtspSocket[1][0]
                    #print(address)
                    port = int(self.rtpPort)

                    packet_list = self.make_rtp_list(data, self.frame_number)
                    print('cold')
                    for packet in packet_list:
                        self.rtpSocket.sendto(packet, (address, port))
                    self.frame_number = self.frame_number + 1
                    if self.frame_number == self.picture_num:
                        self.frame_number = 0

                except:
                    print("Connection Error")


    def make_rtp_list(self,payload,frame_number):
        print('framenumber')

        print('enter')
        packet_list = []
        print('c0')
        remain = len(payload)
        print('c1')
        while remain > 0:
            V = 2
            P = 0
            X = 0
            CC = 0
            M = 0
            PT = 26
            seqNum = frame_number
            SSRC = 0
            if remain <= 10240:
                M = 1
                packet_length = remain
            else:
                packet_length = 10240
            print('haha')
            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum, M, PT, SSRC, payload[0:packet_length])
            packet = rtpPacket.getPacket()
            packet_list.append(packet)
            payload = payload[packet_length:]
            remain = remain - packet_length
            print(remain)
        return packet_list


