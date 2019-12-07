import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
    try:
        server_addr = sys.argv[1]
        server_port = sys.argv[2]
        my_port = sys.argv[3]
    except:
        print ("Error\n")

    window = Tk()
    app = Client(window, server_addr, server_port, my_port)
    app.master.title("Client")
    window.mainloop()