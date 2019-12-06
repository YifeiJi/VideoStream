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
        print ("Error parameters")

    app = QApplication(sys.argv)
    client = Client(None,None, serverAddr, serverPort, rtpPort)
    sys.exit(app.exec_())