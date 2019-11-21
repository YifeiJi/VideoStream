import socket
from random import *
import threading
from RtpPacket import *
class Server:
    def __init__(self, client={}):
        self.client = client
        self.status = 'NOT READY'
        self.filename = None

    def start(self):
        threading.Thread(target=self.listenRtsp).start()

    def listenRtsp(self):
        conn = self.client['rtspSocket'][0]
        while True:
            res = conn.recv(256)
            if res:
                print ("Received:\n" + res)
                self.handleRtsp(res)

    def handleRtsp(self,request):

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
                print('isset')
                input()
                break
            frameNumber = self.client['frameNumber']
            filename = str(frameNumber) + '.jpg'
            f = open(filename,'rb')
            data = f.read()
            if data:
                try:
                    address = self.client['rtspSocket'][1][0]
                    #print(address)
                    port = int(self.client['rtpPort'])
                    #print(port)
                    packet = self.makeRtp(data, frameNumber)
                    #print('packet done')
                    #print(packet)
                    self.client['rtpSocket'].sendto(packet, (address, port))
                    self.client['frameNumber'] = self.client['frameNumber'] + 1
                    if self.client['frameNumber'] == 3:
                        self.client['frameNumber'] = 0
                except:
                    print "Connection Error"

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
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
