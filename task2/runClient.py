import sys
from tkinter import Tk
from Client import Client
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        serverPort = sys.argv[2]
        rtpPort = sys.argv[3]
    except:
        print ("[Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file]\n")


    # root = Tk()
    # button_root = Tk()
    app = QApplication(sys.argv)

    # Create a new client
    client = Client(None,None, serverAddr, serverPort, rtpPort)
    client.show()
    sys.exit(app.exec_())