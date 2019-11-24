import socket
from random import *
import threading
from RtpPacket import *
from Video import Video
from time import *
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
        self.timer = 30
        self.timeout = 30
        self.window_size = 10
        self.current_window_num = 0
        self.firstInWindow = 0
        self.lastInWindow = -1
        self.interval = 0.001
        self.lock = threading.Lock()

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
                # Update state
                print ("SETUP ing")
                try:
                    self.status = 'READY'
                except:
                    self.reply_rtsp('FILE_NOT_FOUND_404', seq)

                # Generate a randomized RTSP session ID
                self.client['session'] = randint(100000, 999999)
                self.client['frameNumber'] = 0
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
            self.reply_rtsp('OK_200', seq)


        elif cmd == 'TEARDOWN':
            self.client['event'].set()
            self.reply_rtsp('OK_200', seq)
            self.client['rtpSocket'].close()

        elif cmd == 'PLAY':
            self.status = 'PLAYING'
            self.client['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client['event'] = threading.Event()
            self.reply_rtsp('OK_200', seq)
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
        if code == 'OK_200':

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
            #self.client['event'].wait(0.01)
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
            conn = self.rtcpSocket

            msg = conn.recv(256)

            if msg:
                #print(msg.decode())
                msg = msg.decode()
                ack_num = int(msg.split(" ")[-1])
                print("Received ACK: ")
                print(ack_num)
                if ack_num >= self.firstInWindow and ack_num <= self.lastInWindow:
                    self.lock.acquire()
                    #self.current_window_num = self.current_window_num - (ack_num - self.firstInWindow + 1)
                    self.firstInWindow = ack_num + 1
                    self.current_window_num = self.lastInWindow - self.firstInWindow + 1
                    self.timer = self.timeout
                    self.lock.release()

    def count_down(self):
        while True:
            #self.client['event'].wait(0.01)
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
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
        for i in range(first, last + 1):
            index = i % self.window_size
            #seq = self.buffer[index].get
            (packet, current_seq) = self.buffer[index]
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
                data = self.video.next_frame()
                self.new_video = False
                if not data:
                    self.video = Video(self.filename)
                    data = self.video.next_frame()
                packet_num = self.cal_packet_num(data)
                packet_list = self.make_rtp_list(data)
                packet_list_index = 0

            if packet_num + self.current_window_num <= self.window_size:
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


                    # print('cur_seq')
                    # print(current_seq)
                    self.lastInWindow = current_seq
                    self.current_window_num = self.lastInWindow - self.firstInWindow + 1  # self.current_window_num + 1
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
                    data = self.video.next_frame()
                packet_num = self.cal_packet_num(data)
                packet_list = self.make_rtp_list(data)
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

    def make_rtp_list(self,payload):
        packet_list = []
        remain = len(payload)

        while remain > 0:

            V = 2
            P = 0
            X = 0
            CC = 0
            M = 0
            PT = 26

            seqNum = self.seqNum
            self.seqNum = (self.seqNum + 1) % 65536
            #frameNum = frameNumber
            SSRC = 0
            if remain <= 10240:
                M = 1

                packet_length = remain
            else:
                packet_length = 10240

            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum, M, PT, SSRC, payload[0:packet_length])
            packet = rtpPacket.getPacket()
            packet_list.append((packet, seqNum))
            payload = payload[packet_length:]
            remain = remain - packet_length
        return packet_list

    def openRtcpPort(self):
        """Open RTCP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        print('begin open')
        self.rtcpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        #self.rtcpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            print('rtcpport')
            print(self.rtcp_port)
            #input()
            self.rtcpSocket.bind(("", self.rtcp_port))

        except:
            print('fail to open port')
        print('successfully open')
