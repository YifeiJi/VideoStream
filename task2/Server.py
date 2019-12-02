import socket
from random import *
import threading
from RtpPacket import *
from Video import Video
from time import *
import os
from preprocess import *

class Server:
    def __init__(self, rtsp_port, client={}):
        print('rtsp_port',rtsp_port)
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
        self.quality = 2
        self.lock = threading.Lock()
        self.video_lock = threading.Lock()
        self.base_cache = 'server-cache'
        if not os.path.exists(self.base_cache):
            os.makedirs(self.base_cache)
        self.movie_list = []
        self.make_movie_list()

    def make_movie_list(self):
        files = os.listdir('.')
        suffix = 'mp4'
        # print(files)
        for item in files:
            s = item
            if s.split('.')[-1] == suffix:
                description_name = s[0] + '_des.txt'
                print(description_name)
                if os.path.exists(description_name):
                    f = open(description_name,'r')
                    description = f.read()
                    f.close()
                else:
                    description = ''

                bullet_name = s[0] + '_bullet.txt'
                print(bullet_name)
                if os.path.exists(bullet_name):
                    f = open(bullet_name, 'r')
                    bullet = f.read()
                    f.close()
                else:
                    bullet = ''

                video = Video(item)
                length = video.get_time()
                full_item = (item, description, bullet,length)
                self.movie_list.append(full_item)

        for item in self.movie_list:
            file_path = os.path.join(self.base_cache, item[0])
            if not os.path.exists(file_path):
                os.makedirs(file_path)
                make_cache(item[0], file_path)


    def start(self):
        threading.Thread(target=self.listen_rtsp).start()

    def listen_rtsp(self):
        try:
            conn = self.client['rtspSocket'][0]
            while True:
                res = conn.recv(256)
                if res:
                    self.handleRtsp(res)
        except:
            return


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
                    self.client['session'] = randint(100000, 999999)
                    self.client['frameNumber'] = 0
                    self.reply_rtsp('List ' + str(self.movie_list), seq)
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
                self.video.set_quality(self.quality)
            self.filename = filename
            self.realname = self.filename
            self.realname = self.realname.split('.')[0]
            total_frame = self.video.get_length()
            height, width = self.video.get_size()
            fps = self.video.get_fps()
            #print(fps)
            #print(str(fps))
            self.reply_rtsp('Length ' + str(total_frame) + ' Height ' + str(height) + ' Width ' + str(width) +
                            ' fps ' + str(fps), seq)


        elif cmd == 'TEARDOWN':
            self.current_window_num = 0
            self.seqNum = 0
            self.firstInWindow = 0
            self.lastInWindow = -1
            self.reply_rtsp('OK_200', seq)
            if 'event' in self.client:
                self.client['event'].set()
            if 'rtpSocket' in self.client:
                self.client['rtpSocket'].close()
            #self.client['rtspSocket'].close()
            self.client['rtspSocket'][0].close()
            if self.rtcpSocket:
                self.rtcpSocket.close()

        elif cmd == 'PLAY':
            print(request)
            quality = int(request[-1])
            print(quality)
            if quality == 1:
                print('set')
                self.video.set_quality(1)
                self.quality = 1
            self.status = 'PLAYING'
            self.client['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client['rtpSocket'].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        #print(code)
        if code[0] == 'L' and code[1] == 'e':
            # length 300
            reply = 'RTSP/1.0 '+ code + '\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])
            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code[0] == 'L' and code[1] == 'i':
            # List ['a.mp4']

            reply = 'RTSP/1.0 '+ str(code) + '\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])
            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code == 'OK_200':

            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.client['session'])

            reply = reply.encode('utf-8')
            connSocket = self.client['rtspSocket'][0]
            connSocket.send(reply)

        elif code == 'FILE_NOT_FOUND_404':
            print ("404 NOT FOUND")
        elif code == 'CON_ERR_500':
            print ("500 CONNECTION ERROR")

    def recvACK(self):
        try:
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

                    elif cmd_list[0] == 'QUA':
                        print(cmd_list)
                        if self.video:
                            self.video_lock.acquire()
                            self.video.set_quality(int(cmd_list[1]))
                            self.quality = int(cmd_list[1])
                            self.video.set_frame(int(cmd_list[2]))
                            self.video_lock.release()

                    elif cmd_list[0] == 'BUL':
                        frame = cmd_list[1]
                        text = cmd_list[2]
                        bullet_file = self.realname + '_bullet.txt'
                        f = open(bullet_file, 'a')
                        f.write(str(frame) + ' ' + text + '\n')
                        f.close()
                    else:
                        pass
        except:
            return
                    #print(cmd_list)


    def count_down(self):
        while True:
            if self.client['event'].isSet():
                break
            if self.current_window_num == 0:
                self.timer = self.timeout
                continue
            sleep(self.interval)
            self.timer = self.timer - 1
            if self.timer == 0:
                self.lock.acquire()
                #print('resend')
                #print(self.firstInWindow, self.lastInWindow)
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
                print('new')
                if self.filename:
                    self.video = Video(self.filename)
                    self.video.set_quality(self.quality)

            if new_data or self.new_video:
                self.video_lock.acquire()
                tuple = self.video.next_frame()
                self.video_lock.release()
                self.new_video = False
                if not tuple:
                    continue

                else:
                    data, frame_num = tuple
                    #print('send:',frame_num)
                print(frame_num)
                if frame_num % self.video.fps == 0:

                    sec = int (frame_num // self.video.fps)
                    audio_file = os.path.join(self.base_cache,self.filename,self.realname + '_' + str(sec) + '.mp3')
                    audio_file = open(audio_file, 'rb')
                    audio = audio_file.read()
                    audio_file.close()
                    packet_num = self.cal_packet_num(data) + 1

                    if self.video.quality == '':
                        quality = 2
                    else:
                        quality = 1

                    packet_list = self.make_rtp_list(data, frame_num, audio, quality)
                else:
                    packet_num = self.cal_packet_num(data)
                    if self.video.quality == '':
                        quality = 2
                    else:
                        quality = 1
                    packet_list = self.make_rtp_list(data, frame_num, None, quality)
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
                return

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
                return


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

    def make_rtp_list(self, payload, frame_num, audio, quality):
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
            #print(packet_length)
            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum, frame_num, M, PT, SSRC, audio, quality)
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
            rtpPacket.encode(V, P, X, CC, seqNum,frame_num, M, PT, SSRC, payload[0:packet_length], quality)
            packet = rtpPacket.getPacket()
            packet_list.append((packet, seqNum))
            payload = payload[packet_length:]
            remain = remain - packet_length
        return packet_list

    def openRtcpPort(self):
        """Open RTCP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server

        self.rtcpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            print(self.rtcp_port)
            self.rtcpSocket.bind(("", self.rtcp_port))

        except:
            print('fail to open port')
        print('successfully open')
