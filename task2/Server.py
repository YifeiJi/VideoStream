import socket
from random import *
import threading
from RtpPacket import *
from Video import Video
from time import *
import os

class Server:
    def __init__(self, rtsp_port, client={}):
        self.rtsp_port = rtsp_port
        self.rtcp_port = self.rtsp_port + 1
        self.client = client
        self.status = 'NOT READY'
        self.filename = None
        self.seqNum = 0
        self.video = None
        self.new_video = False
        self.buffer = []
        self.timer = 20
        self.timeout = 20
        self.window_size = 64
        self.current_window_num = 0
        self.firstInWindow = 0
        self.lastInWindow = -1
        self.interval = 0.01
        self.lock = threading.Lock()
        self.video_lock = threading.Lock()
        self.base_cache = 'server-cache'
        if not os.path.exists(self.base_cache):
            os.makedirs(self.base_cache)

    def start(self):
        threading.Thread(target=self.listen_rtsp).start()

    def listen_rtsp(self):
        conn = self.client['rtspSocket'][0]
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
        #input()
        first_item = request[0].split(' ')

        cmd = first_item[0]
        #print('cmd:',cmd)

        filename = first_item[1]
        #print('filename:',filename)

        seq = request[1].split(' ')[1]
        #print('seq:', seq)

        if cmd == 'SETUP':
            if self.status == 'NOT READY':
                try:
                    movie_list = ['a.mp4', 'b.mp4']
                    print(movie_list)
                    print('str:',str(movie_list))

                    self.client['session'] = randint(100000, 999999)
                    self.client['frameNumber'] = 0
                    self.reply_rtsp('List ' + str(movie_list), seq)
                    self.status = 'READY'
                except:
                    print('except')
                    self.reply_rtsp('FILE_NOT_FOUND_404', seq)

                # Generate a randomized RTSP session ID

                # Send RTSP reply
                self.reply_rtsp('OK_200', seq)

                # Get the RTP/UDP port from the last line
                self.client['rtpPort'] = request[2].split(' ')[3]
                self.openRtcpPort()

            else:
                pass
        elif cmd == 'SETUPMOVIE':
            if self.filename != filename:
                self.video = Video(filename)
            self.filename = filename
            self.realname = self.filename
            self.realname = self.realname.split('.')[0]
            total_frame = self.video.get_length()
            self.reply_rtsp('Length ' + str(total_frame), seq)


        elif cmd == 'TEARDOWN':
            self.current_window_num = 0
            self.firstInWindow = 0
            self.lastInWindow = -1
            self.client['event'].set()
            self.reply_rtsp('OK_200', seq)
            self.client['rtpSocket'].close()

        elif cmd == 'PLAY':
            self.status = 'PLAYING'
            self.client['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client['event'] = threading.Event()
            self.reply_rtsp('OK_200', seq)
            print('start play')
            self.new_video = True
            threading.Thread(target=self.recvACK).start()
            threading.Thread(target=self.count_down).start()
            threading.Thread(target=self.listen_rtsp).start()
            self.send_rtp_gbn()



        elif cmd == 'PAUSE':
            print('pause')
            print(self.status)
            if self.status == 'PLAYING':
                self.status = 'READY'
                self.client['event'].set()
                self.reply_rtsp('OK_200', seq)

        else:
            pass

    def reply_rtsp(self, code, seq):
        print(code)
        if code[0] == 'L' and code[1] == 'e':
            # length 300
            reply = 'RTSP/1.0 '+ code + '\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])
            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code[0] == 'L' and code[1] == 'i':
            # List ['a.mp4']
            print('ddddddd')
            print(code)
            reply = 'RTSP/1.0 '+ str(code) + '\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])
            print('aaa',reply)
            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code == 'OK_200':

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])
            print('reply')
            print(reply)
            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code == 'FILE_NOT_FOUND_404':
            print ("404 NOT FOUND")
        elif code == 'CON_ERR_500':
            print ("500 CONNECTION ERROR")

    def recvACK(self):
        while True:
            if self.client['event'].isSet():
                break
            conn = self.rtcpSocket

            msg = conn.recv(256)

            if msg:
                #print(msg.decode())
                msg = msg.decode()
                cmd_list = msg.split(" ")
                if cmd_list[0] == 'ACK':
                    ack_num = int(cmd_list[-1])
                    #print("Received ACK: ")
                    #print(ack_num)
                    if ack_num >= self.firstInWindow and ack_num <= self.lastInWindow:
                        self.lock.acquire()
                        #self.current_window_num = self.current_window_num - (ack_num - self.firstInWindow + 1)
                        for t in range(self.firstInWindow,ack_num+1):
                            index = t%self.window_size
                            data,ii = self.buffer[index]
                            if t != ii:
                                print('recvackfail',ii,t)
                                #input()
                        self.firstInWindow = ack_num + 1
                        self.current_window_num = self.lastInWindow - self.firstInWindow + 1
                        self.timer = self.timeout
                        self.lock.release()
                elif cmd_list[0] == 'RES':
                    #print(cmd_list)
                    self.status = 'PLAYING'
                    restore_frame = int(cmd_list[1])
                    if self.video:
                        self.video_lock.acquire()
                        self.video.set_frame(restore_frame)
                        self.video_lock.release()
                else:
                    pass
                    #print(cmd_list)


    def count_down(self):
        while True:
            #self.client['event'].wait(0.01)
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
            if self.current_window_num == 0:
                self.timer = self.timeout
                continue
            sleep(self.interval)
            self.timer = self.timer - 1
            if self.timer == 0:
                self.lock.acquire()
                print('resend')
                print(self.firstInWindow, self.lastInWindow)
                self.resend_packets(self.firstInWindow, self.lastInWindow)
                self.timer = self.timeout
                self.lock.release()

        #pass

    def resend_packets(self,first, last):
        if first > last:
            return
        for i in range(first, last + 1):
            index = i % self.window_size
            (packet, current_seq) = self.buffer[index]
            if current_seq != i:
                print('neq',i,current_seq)
            self.send_rtp_packet(packet)


    def send_rtp_gbn(self):
        new_data = True
        packet_list_index = 0
        while True:
            #self.client['event'].wait(0.01)
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
            if not self.video or self.new_video:
                if self.filename:
                    self.video = Video(self.filename)

            if new_data or self.new_video:
                self.video_lock.acquire()
                tuple = self.video.next_frame()
                self.video_lock.release()
                self.new_video = False
                if not tuple:
                    continue
                    # self.video = Video(self.filename)
                    # self.video_lock.acquire()
                    # data, frame_num = self.video.next_frame()
                    # self.video_lock.release()
                else:
                    data, frame_num = tuple
                    print('send:',frame_num)
                if frame_num % self.video.fps == 0:

                    sec = int (frame_num // self.video.fps)
                    audio_file = os.path.join(self.base_cache,self.realname + '_' + str(sec) + '.mp3')
                    audio_file = open(audio_file, 'rb')
                    audio = audio_file.read()
                    packet_num = self.cal_packet_num(data) + 1
                    packet_list = self.make_rtp_list(data, frame_num, audio)
                else:
                    packet_num = self.cal_packet_num(data)
                    packet_list = self.make_rtp_list(data, frame_num,None)
                packet_list_index = 0

            if packet_num - packet_list_index + self.current_window_num <= self.window_size:
                new_data = True
            else:
                new_data = False

            try:
                for i in range(packet_list_index, len(packet_list)):
                    if self.current_window_num == self.window_size:
                        packet_list_index = i
                        break
                    (packet, current_seq) = packet_list[i]
                    if current_seq <= self.lastInWindow:
                        continue
                    self.lock.acquire()
                    if current_seq < self.window_size:
                        self.buffer.append((packet, current_seq))
                    else:
                        index = current_seq % self.window_size
                        self.buffer[index] = (packet, current_seq)
                    self.send_rtp_packet(packet)

                    self.lastInWindow = current_seq
                    self.current_window_num = self.lastInWindow - self.firstInWindow + 1
                    self.lock.release()
            except:
                print("Connection Error")

    def send_rtp(self):
        new_data = True
        packet_list_index = 0
        while True:
            #self.client['event'].wait(0.01)
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
            if not self.video or self.new_video:
                if self.filename:
                    self.video = Video(self.filename)

            if True: #new_data or self.new_video:
                data = self.video.next_frame()
                self.new_video = False
                if not data:
                    self.video = Video(self.filename)
                    data, frame = self.video.next_frame()
                packet_num = self.cal_packet_num(data)
                packet_list = self.make_rtp_list(data, frame)
                packet_list_index = 0

            # if packet_num + self.current_window_num <= self.window_size:
            #     new_data = True
            # else:
            #     new_data = False

            try:
                packet_list_index = 0
                for i in range(packet_list_index, len(packet_list)):
                    # if self.current_window_num == self.window_size:
                    #     packet_list_index = i
                    #     break
                    (packet, current_seq) = packet_list[i]
                    # if current_seq <= self.lastInWindow:
                    #     continue

                    # self.lock.acquire()
                    if current_seq < self.window_size:
                        self.buffer.append((packet, current_seq))
                    else:
                        index = current_seq % self.window_size
                        self.buffer[index] = (packet, current_seq)
                    self.send_rtp_packet(packet)


                    # print('cur_seq')
                    # print(current_seq)
                    # self.lastInWindow = current_seq
                    # self.current_window_num = self.lastInWindow - self.firstInWindow + 1  # self.current_window_num + 1
                    # self.lock.release()
            except:
                print("Connection Error")


    def cal_packet_num(self, data):
        if len(data) == 0:
            return
        ans = len(data) // 10240 + 1
        if len(data) % 10240 == 0:
            ans = ans - 1
        return ans

    def send_rtp_packet(self, packet):
        try:
            address = self.client['rtspSocket'][1][0]
            port = int(self.client['rtpPort'])
            self.client['rtpSocket'].sendto(packet, (address, port))
            self.client['frameNumber'] = self.client['frameNumber'] + 1

        except:
            print("Connection Error")

    def make_rtp_list(self, payload, frame_num, audio):
        packet_list = []
        remain = len(payload)

        if audio:
            V = 2
            P = 0
            X = 0
            CC = 0
            M = 0
            PT = 2

            seqNum = self.seqNum
            self.seqNum = self.seqNum + 1
            # frameNum = frameNumber
            SSRC = 0
            packet_length = len(audio)
            print(packet_length)
            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum, frame_num, M, PT, SSRC, audio)
            packet = rtpPacket.getPacket()
            packet_list.append((packet, seqNum))


        while remain > 0:

            V = 2
            P = 0
            X = 0
            CC = 0
            M = 0
            PT = 1

            seqNum = self.seqNum
            self.seqNum = self.seqNum + 1
            #frameNum = frameNumber
            SSRC = 0
            if remain <= 20460:
                M = 1

                packet_length = remain
            else:
                packet_length = 20460

            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum,frame_num, M, PT, SSRC, payload[0:packet_length])
            packet = rtpPacket.getPacket()
            packet_list.append((packet, seqNum))
            payload = payload[packet_length:]
            remain = remain - packet_length
        return packet_list

    def openRtcpPort(self):
        """Open RTCP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server

        self.rtcpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        #self.rtcpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            #print('rtcpport')
            #print(self.rtcp_port)
            #input()
            self.rtcpSocket.bind(("", self.rtcp_port))

        except:
            print('fail to open port')
        print('successfully open')
