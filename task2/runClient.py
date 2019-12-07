import sys
from Client import Client
from PyQt5.QtWidgets import *

if __name__ == "__main__":
    try:
        my_port = sys.argv[1]
        server_addr = sys.argv[2]
        server_port = sys.argv[3]
    except:
        print ("Error parameters")

    app = QApplication(sys.argv)
    client = Client(None,None, server_addr, server_port, my_port)
    sys.exit(app.exec_())