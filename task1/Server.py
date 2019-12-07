import socket
from random import *
import threading
from RtpPacket import *
import os
class Server:
    def __init__(self, rtsp_socket):
        self.rtsp_socket = rtsp_socket
        self.rtsp_conn_socket = self.rtsp_socket[0]
        self.rtp_socket = None
        self.status = 'NOT READY'
        self.filename = None
        self.base_path = './picture'
        self.picture_list = []
        self.picture_num = 0
        self.frame_number = 0
        self.event = None

    def work(self):
        self.make_picture_list()
        threading.Thread(target=self.listen_rtsp).start()

    def make_picture_list(self):
        files = os.listdir(self.base_path)

        for item in files:
            if '.jpg' in item:
                self.picture_list.append(item)
        self.picture_num = len(self.picture_list)

    def listen_rtsp(self):
        while True:
            res = self.rtsp_conn_socket.recv(256)
            if res:
                # print ("Received:\n")
                # print(res)
                self.handle_rtsp(res)

    def handle_rtsp(self,request):
        request = request.decode('utf-8')
        request = request.split('\n')
        # print('request:',request)
        first_item = request[0].split(' ')

        cmd = first_item[0]
        # print('cmd:',cmd)

        filename = first_item[1]
        # print('filename:',filename)

        seq = request[1].split(' ')[1]
        # print('seq:', seq)

        if cmd == 'SETUP':

            if self.status == 'NOT READY':

                try:
                    self.filename = filename
                    self.status = 'READY'
                except:
                    self.reply_rtsp('ERROR', seq)

                self.session = randint(1000, 9999)
                self.frame_number = 0
                self.reply_rtsp('OK', seq)
                self.rtp_port = request[2].split(' ')[3]
            else:
                pass

        elif cmd == 'TEARDOWN':
            self.event.set()
            self.reply_rtsp('OK', seq)
            self.rtp_socket.close()

        elif cmd == 'PLAY':
            self.status = 'PLAYING'
            self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.event = threading.Event()
            self.reply_rtsp('OK', seq)
            threading.Thread(target=self.listen_rtsp).start()
            self.send_rtp()



        elif cmd == 'PAUSE':
            # print('pause')
            # print(self.status)
            if self.status == 'PLAYING':
                self.status = 'READY'
                self.event.set()
                self.reply_rtsp('OK', seq)
        else:
            pass

    def reply_rtsp(self, code, seq):
        if code == 'OK':

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.session)
            # print('reply')
            # print(reply)
            reply = reply.encode('utf-8')
            self.rtsp_conn_socket.send(reply)
        else:
            print('Error')
            return

    def send_rtp(self):
        while True:
            self.event.wait(0.01)
            if self.event.isSet():
                break
            filename = self.picture_list[self.frame_number]
            filepath = os.path.join(self.base_path,filename)
            f = open(filepath, 'rb')
            data = f.read()
            if data:
                try:
                    address = self.rtsp_socket[1][0]
                    #print(address)
                    port = int(self.rtp_port)

                    packet_list = self.make_rtp_list(data, self.frame_number)

                    for packet in packet_list:
                        self.rtp_socket.sendto(packet, (address, port))
                    self.frame_number = self.frame_number + 1
                    if self.frame_number == self.picture_num:
                        self.frame_number = 0

                except:
                    print("Error")


    def make_rtp_list(self,payload,frame_number):
        packet_list = []
        remain = len(payload)
        while remain > 0:
            version = 2
            padding = 0
            extension = 0
            cc = 0
            marker = 0
            pt = 26
            seqnum = frame_number
            ssrc = 0
            if remain <= 20460:
                marker = 1
                packet_length = remain
            else:
                packet_length = 20460
            rtpPacket = RtpPacket()
            rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload[0:packet_length])
            packet = rtpPacket.getPacket()
            packet_list.append(packet)
            payload = payload[packet_length:]
            remain = remain - packet_length
        return packet_list


