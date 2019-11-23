import socket
from random import *
import threading
from RtpPacket import *
from Video import Video
class Server:
    def __init__(self, client={}):
        self.client = client
        self.status = 'NOT READY'
        self.filename = None
        self.seqNum = 0
        self.video = None

    def start(self):
        threading.Thread(target=self.listenRtsp).start()

    def listenRtsp(self):
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
                    self.status = 'READY'
                except:
                    self.replyRtsp('FILE_NOT_FOUND_404', seq)

                # Generate a randomized RTSP session ID
                self.client['session'] = randint(100000, 999999)
                self.client['frameNumber'] = 0
                # Send RTSP reply
                self.replyRtsp('OK_200', seq)

                # Get the RTP/UDP port from the last line
                self.client['rtpPort'] = request[2].split(' ')[3]
            else:
                pass
        elif cmd == 'SETUPMOVIE':
            if self.filename != filename:
                self.video = Video(filename)
            self.filename = filename
            self.replyRtsp('OK_200', seq)


        elif cmd == 'TEARDOWN':
            self.client['event'].set()
            self.replyRtsp('OK_200', seq)
            self.client['rtpSocket'].close()

        elif cmd == 'PLAY':
            self.status = 'PLAYING'
            self.client["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client['event'] = threading.Event()
            self.replyRtsp('OK_200', seq)
            threading.Thread(target=self.listenRtsp).start()
            self.sendRtp()



        elif cmd == 'PAUSE':
            print('pause')
            print(self.status)
            if self.status == 'PLAYING':
                self.status = 'READY'
                self.client['event'].set()
                self.replyRtsp('OK_200', seq)
        else:
            pass

    def replyRtsp(self, code, seq):
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

    def sendRtp(self):
        #print('send Rtp ready')
        while True:
            self.client['event'].wait(0.01)
            #print('send Rtp start')
            # Stop sending if request is PAUSE or TEARDOWN
            if self.client['event'].isSet():
                break
            frameNumber = self.client['frameNumber']
            # filename = str(frameNumber) + '.jpg'
            # f = open('test.jpg','rb')
            # #f = open(filename, 'rb')
            # data = f.read()
            if not self.video:
                if self.filename:
                    self.video = Video(self.filename)
            data = self.video.next_frame()
            if not data:
                self.video = Video(self.filename)
                data = self.video.next_frame()
            print(len(data))
            if data:
                try:
                    address = self.client['rtspSocket'][1][0]
                    #print(address)
                    port = int(self.client['rtpPort'])

                    packet_list = self.makeRtpList(data,frameNumber)
                    for packet in packet_list:
                        self.client['rtpSocket'].sendto(packet, (address, port))
                    self.client['frameNumber'] = self.client['frameNumber'] + 1
                    if self.client['frameNumber'] == 35:
                        self.client['frameNumber'] = 0

                except:
                    print ("Connection Error")

    def makeRtpList(self,payload,frameNumber):
        packet_list = []
        remain = len(payload)
        print('remain')
        while remain > 0:
            print('remain')
            print(remain)
            V = 2
            P = 0
            X = 0
            CC = 0
            M = 0
            PT = 26
            self.seqNum = self.seqNum + 1
            seqNum = self.seqNum
            frameNum = frameNumber
            SSRC = 0
            if remain <= 10240:
                M = 1

                packet_length = remain
            else:
                packet_length = 10240

            rtpPacket = RtpPacket()
            rtpPacket.encode(V, P, X, CC, seqNum, M, PT, SSRC,frameNum, payload[0:packet_length])
            packet = rtpPacket.getPacket()
            print(rtpPacket.getM())
            packet_list.append(packet)
            payload = payload[packet_length:]
            remain = remain - packet_length
        return packet_list


    def makeRtp(self, payload, frameNbr):

        V = 2
        P = 0
        X = 0
        CC = 0
        M = 0
        PT = 26
        seqNum = frameNbr
        SSRC = 0

        rtpPacket = RtpPacket()
        #print('new packet')
        rtpPacket.encode(V, P, X, CC, seqNum, M, PT, SSRC, payload)
        #print('encodedone')
        # Return the RTP packet
        #print(payload)
        #input()
        #print len(rtpPacket.getPacket())
        #input()
        return rtpPacket.getPacket()
