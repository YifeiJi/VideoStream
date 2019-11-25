from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
from RtpPacket import RtpPacket
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Movie_window(QMainWindow):
    def __init__(self):
        super(Movie_window, self).__init__()
        self.setFixedSize(1600, 900)
        self.setWindowTitle('Play')


class Client(QMainWindow):
    INIT = 0
    READY = 1
    PLAYING = 2

    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    SETUPMOVIE = 4
    update = pyqtSignal(str)
    # Initiation..
    def __init__(self, master, buttonmaster, serveraddr, serverport, rtpport, filename):
        super(Client, self).__init__()
        #self.master = master
        #self.master.protocol("WM_DELETE_WINDOW", self.handler)
        #self.buttonmaster = buttonmaster
        #self.buttonmaster.protocol("WM_DELETE_WINDOW", self.handler)
        self.list = QListWidget(self)

        self.movie_window = Movie_window()
        self.movie_label = QLabel(self.movie_window)
        self.movie_label.setGeometry(50, 50, 500, 500)
        self.movie_label.setScaledContents(True)
        self.movie_label.show()

        self.movie_slider = QSlider(Qt.Horizontal,self.movie_window)
        self.movie_slider.setGeometry(50, 750, 500, 500)
        self.movie_slider.setMinimum(0)
        self.movie_slider.setTickInterval(1)
        self.movie_slider.setTracking(False)
        self.movie_slider.sliderReleased.connect(self.send_rst)
        self.movie_slider.show()


        self.movie_list = ['a.mp4','b.mp4']
        self.createWidgets()
        self.addWidgets(['a.mp4', 'b.mp4'])
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.seq_num = -1
        self.move(300, 300)
        self.setWindowTitle('Client')
        self.update.connect(self.updateMovie)

        # 显示在屏幕上


    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup_button = QPushButton('Setup', self)
        self.setup_button.clicked.connect(self.setupConnection)
        self.setup_button.move(100, 140)
        self.setup_button.resize(150, 50)

        self.play_button = QPushButton('Play', self)
        self.play_button.clicked.connect(self.playMovie)
        self.play_button.move(300, 140)
        self.play_button.resize(150, 50)

        self.pause_button = QPushButton('Pause', self)
        self.pause_button.clicked.connect(self.pauseMovie)
        self.pause_button.move(500, 140)
        self.pause_button.resize(150, 50)

        self.teardown_button = QPushButton('Teardown', self)
        self.teardown_button.clicked.connect(self.exitClient)
        self.teardown_button.move(700, 140)
        self.teardown_button.resize(150, 50)

    def addWidgets(self, name_list):
        """Build GUI."""
        # Create Setup button
        self.list.show()
        self.list.move(530, 200)
        self.list.resize(480, 650)
        self.list.itemDoubleClicked.connect(self.setupMovie)

        for name in name_list:
            #icon_name = 'file.jpg' if isfile else 'folder.jpg'
            item = QListWidgetItem(name)
            self.list.addItem(item)

    def setupConnection(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def setupMovie(self,item):
        """Setup button handler."""
        filename = item.text()
        print(filename)
        self.fileName = filename
        self.sendRtspRequest(self.SETUPMOVIE)


    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        # self.master.destroy()  # Close the gui window
        # self.buttonmaster.destroy()
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
        except:
            pass
        #self.destroy()

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        print(self.state == self.READY)
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets


            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)
            self.movie_window.show()

    def sendACK(self, num):
        # self.client['rtpSocket'].sendto(packet, (address, port))

        message = 'ACK ' + str(num)
        #print(message)
        # print('sendAck')
        self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))

    def send_rst(self):

        # self.client['rtpSocket'].sendto(packet, (address, port))
        num = self.movie_slider.sliderPosition()
        message = 'RES ' + str(num)
        print(message)
        #input()
        self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))

    def listenRtp(self):
        """Listen for RTP packets."""
        payload = None
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    m = rtpPacket.getM()

                    current_seq_num = rtpPacket.seqNum()

                #print(current_seq_num, self.seq_num)
                # input()
                if current_seq_num == self.seq_num + 1:  # Discard the late packet
                    self.seq_num = current_seq_num
                    if not payload:
                        payload = rtpPacket.getPayload()
                    else:
                        payload = payload + rtpPacket.getPayload()
                    if m == 1:
                        # print('m=1')
                        current_frame_num = rtpPacket.framenum()
                        #print('frame', current_frame_num)
                        if not self.movie_slider.isSliderDown():
                            self.movie_slider.setValue(current_frame_num)
                        name = self.writeFrame(payload)

                        self.update.emit(name)
                        #self.updateMovie(self.writeFrame(payload))
                        payload = None
                else:
                    self.sendACK(self.seq_num)
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        # imageFile = 'test.jpg'
        #print(imageFile)

        #self.screen = QGraphicsView(self.movie_window)
        #jpg = QPixmap(imageFile)
        #print(len(jpg))
        #self.label = QLabel('haha',self.movie_window)
        #self.label.setPixmap(jpg)
        #self.label.show()
        #self.label.configure(image=photo, height=600)
        #self.label.image = photo

        # window_pale = QPalette()
        #         # window_pale.setBrush(self.backgroundRole(), QBrush(QPixmap(imageFile)))
        #         # self.movie_window.setPalette(window_pale)
        pix = QPixmap(imageFile)
        #self.movie_label
        #self.lab.setGeometry(50, 50, 300, 200)
        #pixmap = QPixmap('F:\A_code\PyQT_Demo\\1.png')
        self.movie_label.setPixmap(pix)




    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(
                self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
            self.openRtpPort()

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # SetupMovie request
        elif requestCode == self.SETUPMOVIE:

            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            request = 'SETUPMOVIE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.SETUPMOVIE

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            self.rtspSeq += 1
            request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.TEARDOWN
        else:
            return

        # Send the RTSP request using rtspSocket.
        #print(request)
        self.rtspSocket.send(request.encode())

        #print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown

            if self.requestSent == self.TEARDOWN:
                if self.playEvent:
                    self.playEvent.set()
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                return
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        #print('Received:')
        #print(data)
        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])

        filename_list = []
        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                p = lines[0].split(' ')
                if p[1] == 'Length':
                    length = int(p[2])
                    print(length)
                    self.movie_slider.setMaximum(length)

                elif int(p[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # Update RTSP state.
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server

        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user

            self.rtpSocket.bind(("", self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)
        print('successfully open')

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
