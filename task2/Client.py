from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
from time import *
from random import *
import socket, threading, sys, traceback, os
from RtpPacket import RtpPacket
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from playsound import playsound
import subprocess

stor = {}
bullet_store = {}
restore_point_store = {}

# CACHE_FILE_NAME = "cache-"
# CACHE_FILE_EXT = ".jpg"
txt_color = [
    '#4D4DFF', '#FF6EC7', '#00009C','#23238E',
    '#426F42', '#7F00FF', '#7FFF00', '#70DBDB',
    '#EBC79E', '#CFB53B', '#FF7F00', '#FF2400',
    '#DB70DB','#DB7093', '#A68064', '#2F2F4F'
              ]


class Bullet_label(QLabel):
    def __init__(self,parent,init_frame,limit,limit_y):
        super(Bullet_label, self).__init__()
        self.setParent(parent)
        x = int(random() * limit * 0.2)
        y = int(random() * limit_y * 0.9)
        self.color = randint(0, 11)
        self.move(x,y)
        self.v_x = randint(5,10)
        self.init_frame = init_frame
        self.limit = limit
        self.setStyleSheet('font:bold;font-size:40px;color:' + txt_color[self.color])
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def update(self, frame):
        self.setGeometry(self.v_x * (frame-self.init_frame),self.y(),self.width(), self.height())
        if self.x() + self.width() > self.limit or self.x() < 0:
            self.hide()
        else:
            self.show()


class Movie_window(QMainWindow):
    def __init__(self):
        super(Movie_window, self).__init__()
        self.setWindowTitle('Play')
        self.desktop = QApplication.desktop()
        self.screen_width = self.desktop.width()
        self.screen_height = self.desktop.height()
        self.setFixedHeight(self.screen_height * 0.8)
        self.setFixedWidth(self.screen_width * 0.8)
        self.movie_width = self.screen_width * 0.5
        self.movie_height = self.screen_height * 0.7
        self.background_label = QLabel(self)
        self.background_label.setFrameShape(QFrame.Box)
        self.background_label.setStyleSheet('border-width: 1px;border-style: solid;border - color: rgb(255, 170, 0);background - color: rgb(100, 149, 237);')
        self.background_label.setGeometry(0,0,self.movie_width,self.movie_height)
        self.background_label.hide()

class Client(QMainWindow):
    INIT = 0
    READY = 1
    PLAYING = 2
    PAUSED = 3

    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    SETUPMOVIE = 4
    update = pyqtSignal()
    add_sig = pyqtSignal()
    # Initiation..
    def __init__(self, master, buttonmaster, serveraddr, serverport, rtpport):
        super(Client, self).__init__()
        self.connected = False
        self.fullscreen_mode = False
        self.grabKeyboard()
        self.movie_window = Movie_window()
        self.movie_window.show()
        self.setFocusPolicy(Qt.StrongFocus)
        self.restore_button = None
        self.setup_button = QPushButton('开始体验', self.movie_window)
        self.setup_button.clicked.connect(self.setupConnection)

        self.setup_button.resize(self.movie_window.width() * 0.3, self.movie_window.height()*0.3)
        self.setup_button.move(0.5* self.movie_window.width()-0.5* self.setup_button.width(),0.5* self.movie_window.height()-0.5* self.setup_button.height())
        self.setup_button.show()
        self.fullscreen_label = QLabel()
        self.fullscreen_label.setAlignment(Qt.AlignCenter)
        self.fullscreen_label.showFullScreen()
        self.fullscreen_label.setStyleSheet('background-color: rgb(0, 0, 0)')
        self.fullscreen_label.hide()

        # self.movie_slider = QSlider(Qt.Horizontal,self.movie_window)
        # self.movie_slider.setGeometry(0,self.movie_window.movie_height+0.3*(self.movie_window.height()-self.movie_window.movie_height),self.movie_window.movie_width,0.5*(self.movie_window.height()-self.movie_window.movie_height))
        # self.movie_slider.setMinimum(0)
        # self.movie_slider.setTickInterval(1)
        # self.movie_slider.setTracking(False)
        # self.movie_slider.sliderReleased.connect(self.send_rst)
        # self.movie_slider.show()
        #
        # self.speed_btn_group = QButtonGroup(self.movie_window)
        # self.speed_btn1 = QRadioButton("0.5倍速", self.movie_window)
        # self.speed_btn1.setGeometry(0.63*self.movie_window.width(),0.1*self.movie_window.height(),0.13*self.movie_window.width(),0.08*self.movie_window.height())
        # self.speed_btn1.show()
        # self.speed_btn_group.addButton(self.speed_btn1)
        #
        # self.speed_btn2 = QRadioButton("1 倍速", self.movie_window)
        # self.speed_btn2.setChecked(True)
        # self.speed_btn2.setGeometry(0.63*self.movie_window.width(),0.15*self.movie_window.height(),0.13*self.movie_window.width(),0.08*self.movie_window.height())
        # self.speed_btn2.show()
        # self.speed_btn_group.addButton(self.speed_btn2)
        #
        # self.speed_btn3 = QRadioButton("1.5倍速", self.movie_window)
        # self.speed_btn3.setGeometry(0.63*self.movie_window.width(),0.2*self.movie_window.height(),0.13*self.movie_window.width(),0.08*self.movie_window.height())
        # self.speed_btn3.show()
        # self.speed_btn_group.addButton(self.speed_btn3)
        #
        # self.speed_btn4 = QRadioButton("2 倍速",  self.movie_window)
        # self.speed_btn4.setGeometry(0.63*self.movie_window.width(),0.25*self.movie_window.height(),0.12*self.movie_window.width(),0.08*self.movie_window.height())
        # self.speed_btn4.show()
        # self.speed_btn_group.addButton(self.speed_btn4)
        #
        #
        # self.quality_btn1 = QRadioButton("低清",self.movie_window)
        # self.quality_btn1.setGeometry(0.63*self.movie_window.width(),0.35*self.movie_window.height(),0.12*self.movie_window.width(),0.08*self.movie_window.height())
        # self.quality_btn1.show()
        # self.quality_btn1.clicked.connect(self.send_quality)
        #
        # self.quality_btn2 = QRadioButton("高清",self.movie_window)
        # self.quality_btn2.setChecked(True)
        # self.quality_btn2.setGeometry(0.63*self.movie_window.width(),0.4*self.movie_window.height(),0.12*self.movie_window.width(),0.08*self.movie_window.height())
        # self.quality_btn2.show()
        # self.quality_btn2.clicked.connect(self.send_quality)
        # self.quality = ''
        self.bullet_list = []
        self.movie_list = []
        self.time = {}
        #self.createWidgets()
        self.serverAddr = serveraddr
        self.init_serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = ''
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.seq_num = -1
        self.frame_to_play = 0
        self.movie_length = 0
        self.restore_point = 0
        #self.move(300, 300)
        self.setWindowTitle('Client')
        self.update.connect(self.updateMovie)
        self.add_sig.connect(self.addWidgets)

        self.frame_to_play = 0
        self.require_buffer = True
        self.buffer = 50
        self.fps = 24
        self.interval = 1 / self.fps
        self.recv_v = 0
        self.last_frame_time = 0
        self.alpha = 0.9
        # 显示在屏幕上

        self.cache_base = 'client-cache'
        if not os.path.exists(self.cache_base):
            os.makedirs(self.cache_base)
        self.hide()

    def createWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.setup_button.hide()
        self.movie_window.background_label.show()

        self.play_button = QPushButton('开始播放', self.movie_window)
        self.play_button.clicked.connect(self.playMovie_wrapper(0))
        self.play_button.setGeometry(self.movie_window.width()*0.7,self.movie_window.movie_height+0.0*(self.movie_window.height()-self.movie_window.movie_height),0.08*self.movie_window.width(),0.05*self.movie_window.height())
        #self.play_button.show()


        self.pause_button = QPushButton('暂停播放', self.movie_window)
        self.pause_button.clicked.connect(self.pauseMovie)
        self.pause_button.setGeometry(self.movie_window.width()*0.8,self.movie_window.movie_height,0.08*self.movie_window.width(),0.05*self.movie_window.height())

        self.fullscreen_button = QPushButton('切换全屏', self.movie_window)
        self.fullscreen_button.clicked.connect(self.set_fullscreen)
        self.fullscreen_button.setGeometry(self.movie_window.width() * 0.9, self.movie_window.movie_height, 0.08 * self.movie_window.width(),
                                      0.05 * self.movie_window.height())


        self.teardown_button = QPushButton('Teardown', self)
        self.teardown_button.clicked.connect(self.exitClient)
        self.teardown_button.move(300, 40)
        self.teardown_button.resize(150, 50)

        self.movie_label = QLabel(self.movie_window)
        self.movie_label.show()

        self.movie_slider = QSlider(Qt.Horizontal, self.movie_window)
        self.movie_slider.setGeometry(0, self.movie_window.movie_height + 0.3 * (
                    self.movie_window.height() - self.movie_window.movie_height), self.movie_window.movie_width,
                                      0.5 * (self.movie_window.height() - self.movie_window.movie_height))
        self.movie_slider.setMinimum(0)
        self.movie_slider.setTickInterval(1)
        self.movie_slider.setTracking(False)
        self.movie_slider.sliderReleased.connect(self.send_rst)
        self.movie_slider.show()

        self.speed_btn_group = QButtonGroup(self.movie_window)
        self.speed_btn1 = QRadioButton("0.5 倍速", self.movie_window)
        self.speed_btn1.setGeometry(0.63 * self.movie_window.width(), 0.1 * self.movie_window.height(),
                                    0.13 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.speed_btn1.show()
        self.speed_btn_group.addButton(self.speed_btn1)

        self.speed_btn2 = QRadioButton("1.0 倍速", self.movie_window)
        self.speed_btn2.setChecked(True)
        self.speed_btn2.setGeometry(0.63 * self.movie_window.width(), 0.15 * self.movie_window.height(),
                                    0.13 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.speed_btn2.show()
        self.speed_btn_group.addButton(self.speed_btn2)

        self.speed_btn3 = QRadioButton("1.5 倍速", self.movie_window)
        self.speed_btn3.setGeometry(0.63 * self.movie_window.width(), 0.2 * self.movie_window.height(),
                                    0.13 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.speed_btn3.show()
        self.speed_btn_group.addButton(self.speed_btn3)

        self.speed_btn4 = QRadioButton("2.0 倍速", self.movie_window)
        self.speed_btn4.setGeometry(0.63 * self.movie_window.width(), 0.25 * self.movie_window.height(),
                                    0.12 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.speed_btn4.show()
        self.speed_btn_group.addButton(self.speed_btn4)

        self.quality_btn1 = QRadioButton("低清", self.movie_window)
        self.quality_btn1.setGeometry(0.63 * self.movie_window.width(), 0.35 * self.movie_window.height(),
                                      0.12 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.quality_btn1.show()
        self.quality_btn1.clicked.connect(self.send_quality)

        self.quality_btn2 = QRadioButton("高清", self.movie_window)
        self.quality_btn2.setChecked(True)
        self.quality_btn2.setGeometry(0.63 * self.movie_window.width(), 0.4 * self.movie_window.height(),
                                      0.12 * self.movie_window.width(), 0.08 * self.movie_window.height())
        self.quality_btn2.show()
        self.quality_btn2.clicked.connect(self.send_quality)
        self.quality = ''

    def addWidgets(self):
        """Build GUI."""
        # Create Setup button
        self.createWidgets()
        self.list = QListWidget(self.movie_window)
        name_list = eval(self.movie_list)
        print(name_list)

        #self.list.itemDoubleClicked.connect(self.setupMovie)
        self.list.show()

        for tup in name_list:
            print(tup)
            name, des, bullet,length = tup
            self.time[name] = length
            if not des:
                des = ''
            restore_point_store[name] = 0

            if bullet:
                bullet_lines = bullet.split('\n')
                bullet_dict = {}
                for line in bullet_lines:
                    line = line.split(' ')
                    print(line)
                    if len(line) <= 1:
                        continue
                    frame_number = int(line[0])
                    content = ' '.join(line[1:])
                    if frame_number not in bullet_dict:
                        bullet_dict[frame_number] = [content]
                    else:
                        bullet_dict[frame_number].append(content)
                print(bullet_dict)
                bullet_store[name] = bullet_dict
            else:
                bullet_store[name] = {}
            print(bullet_store)
            item_widget = QWidget(self)
            item_layout = QVBoxLayout()

            control_layout = QHBoxLayout()
            des_layout = QHBoxLayout()

            name_label = QLabel(name,self)
            control_layout.addWidget(name_label, alignment=Qt.AlignLeft)

            play_button = QPushButton(self)
            play_button.setText('进入')
            play_button.clicked.connect(self.setupMovie_wrapper(name))
            control_layout.addWidget(play_button, alignment=Qt.AlignRight)
            item_layout.addLayout(control_layout)

            description_label = QLabel(des, self)
            des_layout.addWidget(description_label, alignment=Qt.AlignLeft)

            m, s = divmod(length, 60)
            h, m = divmod(m, 60)
            time_str = '时长：%02d:%02d:%02d' % (h, m, s)
            time_label = QLabel(time_str, self)
            des_layout.addWidget(time_label, alignment=Qt.AlignRight)

            item_layout.addLayout(des_layout)

            item_widget.setLayout(item_layout)
            item = QListWidgetItem()
            item.setSizeHint(item_layout.sizeHint())
            #item.setSizeHint(QSize(200, 50))
            self.list.addItem(item)
            self.list.setItemWidget(item, item_widget)
            self.list.setGeometry(self.movie_window.width()*0.7,0,self.movie_window.width()*0.28,self.movie_window.movie_height * 0.75)

            self.bullet_editor = QLineEdit(self.movie_window)
            self.bullet_editor.setGeometry(self.movie_window.width()*0.7,self.movie_window.movie_height * 0.78,self.movie_window.width()*0.28,self.movie_window.movie_height * 0.15)
            self.bullet_editor.show()

            self.bullet_send = QPushButton(self.movie_window)
            self.bullet_send.setText('发送弹幕')
            self.bullet_send.setGeometry(self.movie_window.width() * 0.7, self.movie_window.movie_height * 0.95,
                                           self.movie_window.width() * 0.28, self.movie_window.movie_height * 0.03)
            self.bullet_send.clicked.connect(self.send_bullet)
            self.bullet_send.hide()

    def setupConnection(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def setupMovie_wrapper(self,filename):
        def setupMovie():
            """Setup button handler."""
            #print(filename)
            self.buffer = 50
            self.fileName = filename
            self.restore_point = restore_point_store[filename]
            self.realname = filename.split('.')[0]
            if self.fileName in bullet_store:
                self.bullet = bullet_store[self.fileName]
            else:
                self.bullet = {}

            for item in self.bullet_list:
                item.hide()
            self.bullet_list = []
            for dict_item in self.bullet:
                # print('dict_item',dict_item)
                frame = int(dict_item)
                text_list = self.bullet[dict_item]
                limit = self.movie_window.movie_width
                limit_y = self.movie_window.movie_height
                for text in text_list:
                    bullet_label = Bullet_label(self.movie_window,frame,limit,limit_y)
                    bullet_label.setText(text)
                    bullet_label.adjustSize()
                    bullet_label.hide()
                    self.bullet_list.append(bullet_label)

            self.sendRtspRequest(self.SETUPMOVIE)
            self.frame_to_play = 0
            self.movie_slider.setValue(0)

            self.movie_label.setPixmap(QPixmap(""))
            if self.state == self.PLAYING:
                self.state = self.PAUSED
            self.movie_window.show()
            self.play_button.show()
            self.pause_button.show()
            self.fullscreen_button.show()
            self.bullet_send.show()
            if self.restore_point != 0:

                time = int(self.restore_point * self.movie_time / self.movie_length )

                m, s = divmod(time, 60)
                h, m = divmod(m, 60)
                time_str = '上次观看到：%02d:%02d:%02d, 点击从此处播放' % (h, m, s)
                self.restore_button = QPushButton(time_str, self.movie_window)
                self.restore_button.clicked.connect(self.playMovie_wrapper(self.restore_point))
                self.restore_button.setGeometry(self.movie_window.width() * 0.75,
                                                self.movie_window.movie_height + 0.6 * (
                                                        self.movie_window.height() - self.movie_window.movie_height),
                                                0.08 * self.movie_window.width(), 0.05 * self.movie_window.height())


                print(self.restore_point, self.movie_time, self.movie_length)
                print(time_str)
                # self.restore_label = QLabel(time_str,self.movie_window)
                # self.restore_label.setGeometry(self.movie_window.width() * 0.8,
                #                                 self.movie_window.movie_height + 0.3 * (
                #                                         self.movie_window.height() - self.movie_window.movie_height),
                #                                 0.08 * self.movie_window.width(), 0.05 * self.movie_window.height())
                self.restore_button.adjustSize()
                self.restore_button.show()
                #self.restore_label.show()
        return setupMovie

    def exitClient(self):
        """Teardown button handler."""

        self.sendRtspRequest(self.TEARDOWN)
        self.seq_num = -1
        try:
            pass
            #os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
        except:
            pass
        #self.destroy()

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            #self.sendRtspRequest(self.PAUSE)
            self.state = self.PAUSED


    def playMovie_wrapper(self,restore_point):
        def playMovie():
            """Play button handler."""
            if self.restore_button:
                self.restore_button.hide()
            self.restore_point = restore_point
            if self.state == self.READY:
                # Create a new thread to listen for RTP packets
                threading.Thread(target=self.listenRtp).start()
                self.require_buffer = True
                self.frame_to_play = restore_point
                self.movie_slider.setValue(self.frame_to_play)
                self.playEvent = threading.Event()
                self.playEvent.clear()
                self.sendRtspRequest(self.PLAY)
                self.send_rst()
                threading.Thread(target=self.timer).start()
            elif self.state == self.PAUSED:
                if restore_point > 0:
                    self.frame_to_play = restore_point
                self.movie_slider.setValue(self.frame_to_play)
                self.state = self.PLAYING
                self.send_rst()
        return playMovie

    def playMovie(self):
        """Play button handler."""
        if self.restore_button:
            self.restore_button.hide()
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.require_buffer = True
            # self.frame_to_play = self.restore_point
            self.movie_slider.setValue(self.frame_to_play)
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)
            self.send_rst()
            threading.Thread(target=self.timer).start()
        elif self.state == self.PAUSED:
            # self.frame_to_play = self.restore_point
            self.movie_slider.setValue(self.frame_to_play)
            self.state = self.PLAYING
            self.send_rst()

    def timer(self):
        while True:
            if self.playEvent.isSet():
                break
            self.update.emit()
            num = 1
            if self.speed_btn1.isChecked():
                num = 0.5
            if self.speed_btn3.isChecked():
                num = 1.5
            if self.speed_btn4.isChecked():
                num = 2.0
            sleep(self.interval / num)


    def sendACK(self, num):

        message = 'ACK ' + str(num)
        #print(message)
        # print('sendAck')
        self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))

    def send_quality(self):
        if self.quality_btn1.isChecked():
            self.quality = '-low'
        if self.quality_btn2.isChecked():
            self.quality = ''
        num = self.movie_slider.sliderPosition()
        while num < self.movie_length:
            name = self.get_name(num)
            if name not in stor:
                break
            num = num + 1
        if num == self.movie_length:
            num = num - 1
        if self.quality_btn1.isChecked():
            message = 'QUA 1 ' + str(num)

        if self.quality_btn2.isChecked():
            message = 'QUA 2 ' + str(num)
            self.quality = ''
        self.require_buffer = True
        print(message)
        self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))

        return

    def send_bullet(self):
        num = self.movie_slider.sliderPosition()
        text = self.bullet_editor.text()
        new_bullet = Bullet_label(self.movie_window,num,self.movie_window.movie_width,self.movie_window.movie_height)
        new_bullet.setText(text)
        new_bullet.adjustSize()
        self.bullet_list.append(new_bullet)
        #
        # full_new_bullet = Bullet_label(self.fullscreen_label, num, self.movie_window.screen_width, self.movie_window.screen_height)
        # full_new_bullet.setText(text)
        # full_new_bullet.adjustSize()
        # self.full_bullet_list.append(full_new_bullet)

        bullet_dict = bullet_store[self.fileName]
        if num not in bullet_dict:
            bullet_dict[num] = [text]
        else:
            bullet_dict[num].append(text)
        bullet_store[self.fileName] = bullet_dict

        message = 'BUL ' + str(num) + ' ' + text
        print(message)
        self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))



    def send_rst(self):
        # self.client['rtpSocket'].sendto(packet, (address, port))
        num = self.movie_slider.sliderPosition()
        self.frame_to_play = num

        # for item in self.bullet_list:
        #     item.hide()
        while num < self.movie_length:
            name = self.get_name(num)
            if name not in stor:
                message = 'RES ' + str(num)
                print(message)
                self.last_frame_time = 0
                self.recv_v = 0
                self.rtpSocket.sendto(message.encode(), (self.serverAddr, self.serverPort + 1))
                break
            num = num + 1
        # if self.state == self.PLAYING:
        #     self.state = self.PAUSED

    def listenRtp(self):
        """Listen for RTP packets."""
        payload = None
        while True:
            if self.playEvent.isSet():
                break

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
                    type = rtpPacket.payloadType()
                    if type == 2:
                        current_frame_num = rtpPacket.framenum()
                        sec = int (current_frame_num // self.fps) + 1
                        #print('audio',sec)
                        file_name = self.realname + '_' + str(sec) + '.mp3'
                        file_name = os.path.join(self.cache_base, file_name)
                        f = open(file_name,'wb')
                        f.write(rtpPacket.getPayload())
                        continue
                    if not payload:
                        payload = rtpPacket.getPayload()
                    else:
                        payload = payload + rtpPacket.getPayload()
                    if m == 1:
                        # print('m=1')
                        cur_time = time()
                        if self.last_frame_time == 0:
                            self.last_frame_time = cur_time

                        time_expired = cur_time - self.last_frame_time
                        self.last_frame_time = cur_time

                        if self.recv_v == 0:
                            self.recv_v = time_expired
                        self.recv_v = self.recv_v * self.alpha + time_expired * (1 - self.alpha)
                        print(self.recv_v)
                        current_frame_num = rtpPacket.framenum()

                        if self.interval < self.recv_v and self.require_buffer:
                            buffer_in_need = (self.movie_length - self.frame_to_play) * (self.recv_v - self.interval) / self.recv_v
                            # print('here')
                            #                             # print(self.buffer)
                            #                             # print(buffer_in_need)

                            # if int(buffer_in_need) > self.buffer:
                            #     self.buffer = self.buffer + 1
                            # if self.buffer < 10:
                            #     self.buffer = 10
                        #     input()
                        #     if buffer_in_need > self.buffer:
                        #         self.buffer = int(buffer_in_need)


                        quality = rtpPacket.quality()
                        if quality == 1:
                            quality = '-low'
                        else:
                            quality = ''
                        name = self.writeFrame(payload, self.fileName, current_frame_num,quality)

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

    def get_name(self,frame_num):
        name = str(self.sessionId) + self.fileName + '-' + str(frame_num) + self.quality + '.jpg'
        #print(name)
        return name

    def writeFrame(self, data, filename, current_frame_num, quality):
        global stor
        """Write the received frame to a temp image file. Return the image file."""
        cachename = str(self.sessionId) + filename + '-' + str(current_frame_num) + quality + '.jpg'
        file_path = os.path.join(self.cache_base, cachename)
        file = open(file_path, "wb")
        file.write(data)
        file.close()
        stor[cachename] = data
        return cachename

    def set_fullscreen(self):
        self.fullscreen_mode = True
        for item in self.bullet_list:
            item.setParent(self.fullscreen_label)
            item.limit = self.movie_window.screen_width
            item.setAttribute(Qt.WA_TranslucentBackground, True)
        self.fullscreen_label.show()
        self.movie_window.hide()



    def playAudio(self,filename):
        print(filename)
        filepath = os.path.join(self.cache_base, filename)
        #print(filepath)
        if os.path.exists(filepath):
            playsound(filepath,block=False)
        #playsound(filename)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            if self.fullscreen_mode:
                self.fullscreen_mode = False
                self.fullscreen_label.hide()
                self.movie_window.show()
                for item in self.bullet_list:
                    item.setParent(self.movie_window)
                    item.limit = self.movie_window.movie_width
        elif e.key() == Qt.Key_Space:
            if self.fullscreen_mode and self.state == self.PLAYING:
                self.pauseMovie()
                self.state = self.PAUSED
            elif self.fullscreen_mode and self.state == self.PAUSED:
                self.playMovie()
                self.state = self.PLAYING



    def updateMovie(self):
        """Update the image file as video frame in the GUI."""
        if self.state != self.PLAYING:
            return
        if self.movie_length == self.frame_to_play:
            return
        if self.require_buffer:
            buffer_ok = True
            print(self.buffer)
            up = self.frame_to_play + self.buffer
            if up > self.movie_length - 1:
                up = self.movie_length - 1
            for i in range(self.frame_to_play, up):
                key = self.get_name(i)
                #print(key)
                if key not in stor:
                    buffer_ok = False
                    break
            if buffer_ok:
                self.require_buffer = False
        else:
            if self.frame_to_play % self.fps == 0:
                sec = self.frame_to_play // self.fps
                audio_name = self.realname + '_' + str(sec) + '.mp3'
                threading.Thread(target=self.playAudio,args=(audio_name,)).start()


            pixmap = QPixmap()
            imageFile = self.get_name(self.frame_to_play)
            if imageFile in stor:
                data = stor[imageFile]
                pixmap.loadFromData(data, "JPG")

                if self.fullscreen_mode:

                    new_pixmap = pixmap.scaled(self.movie_width * self.full_multiply, self.movie_height * self.full_multiply, \
                                               Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    self.fullscreen_label.setPixmap(new_pixmap)
                    for item in self.bullet_list:
                        item.update(self.frame_to_play)
                else:
                    new_pixmap = pixmap.scaled(self.movie_width * self.multiply, self.movie_height * self.multiply, \
                                               Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                    self.movie_label.setPixmap(new_pixmap)
                    for item in self.bullet_list:
                        item.update(self.frame_to_play)
                if not self.movie_slider.isSliderDown():
                    self.movie_slider.setValue(self.frame_to_play)
                self.frame_to_play = self.frame_to_play + 1
                restore_point_store[self.fileName] = self.frame_to_play
            else:
                print('cold')
                pass
                #self.require_buffer = True





    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            print(self.init_serverPort)
            self.rtspSocket.connect((self.serverAddr, self.init_serverPort))
            print('connect')
            self.serverPort = self.rtspSocket.recv(256).decode("utf-8")
            print(self.serverPort)
            self.serverPort = self.serverPort.split(' ')[-1]
            print(self.serverPort)
            self.serverPort = int(self.serverPort)
            print(self.serverPort)
            self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rtspSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.rtspSocket.connect((self.serverAddr, self.serverPort))

        except:
            tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)
            return
        self.connected = True

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        #print('play request', requestCode == self.PLAY)
        #print('play request 2', self.state == self.READY)

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            if not self.connected:
                self.connectToServer()
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
        elif requestCode == self.SETUPMOVIE and self.state != self.INIT:
            self.rtspSeq += 1
            # Write the RTSP request to be sent.
            request = 'SETUPMOVIE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.SETUPMOVIE

        # Play request

        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            if self.quality == '':
                request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId) + '\n' + '2'
            else:
                request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                    self.sessionId) + '\n' + '1'
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(
                self.sessionId)
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            self.state == self.INIT
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
        try:
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
                    self.state = self.INIT
                    self.connected = False
                    return
        except:
            if self.requestSent == self.TEARDOWN:
                if self.playEvent:
                    self.playEvent.set()
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
            return


    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        #print('Received:')
        #print(data)

        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])


        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                p = lines[0]
                p = p.split(' ')
                if p[1] == 'Length':
                    length = int(p[2])
                    print(length)
                    height = int(p[4])
                    print(height)
                    width = int(p[6])
                    self.fps = int(p[8])
                    self.interval = 1/self.fps
                    self.movie_slider.setMaximum(length)
                    self.movie_length = length
                    self.movie_time = self.time[self.fileName]
                    self.movie_height = height
                    self.movie_width = width
                    multiply_height = self.movie_window.movie_height/self.movie_height
                    multiply_width = self.movie_window.movie_width/self.movie_width
                    full_multiply_height = self.movie_window.screen_height / self.movie_height
                    full_multiply_width = self.movie_window.screen_width / self.movie_width

                    if multiply_height > multiply_width:
                        self.multiply = multiply_width
                        margin = (self.movie_window.movie_height - self.multiply * self.movie_height) * 0.5
                        self.movie_label.setGeometry(0,margin, self.movie_width * self.multiply,self.movie_height * self.multiply)
                    else:
                        self.multiply = multiply_height
                        margin = (self.movie_window.movie_width - self.multiply * self.movie_width) * 0.5
                        self.movie_label.setGeometry(margin, 0,self.movie_width * self.multiply,self.movie_height * self.multiply)

                    if full_multiply_height > full_multiply_width:
                        self.full_multiply = full_multiply_width
                    else:
                        self.full_multiply = full_multiply_height

                elif p[1] == 'List':
                    p = lines[0]
                    print(p)
                    p = p.split(' ')
                    print('p',p)
                    p = ' '.join(p[2:])
                    print('newp',p)
                    self.movie_list = p
                    print('list:', p)
                    self.add_sig.emit()

                elif int(p[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # Update RTSP state.
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                        self.playEvent = threading.Event()
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
            #tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)
            print('cannot open')
        print('successfully open')

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
