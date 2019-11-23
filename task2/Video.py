import numpy as np

import cv2



class Video:
    def __init__(self,filename):
        self.filename = filename
        self.frame_number = 0
        self.file = open(filename,'rb')
        self.cap = cv2.VideoCapture(filename)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def next_frame(self):
        self.frame_number = self.frame_number + 1

        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret == True:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return None
                cv2.imwrite('temp.jpg', frame)
                f = open('temp.jpg','rb')

                return f.read()
            else:
                return None



video = Video('demo.mp4')
data = video.next_frame()
f = open('test3.jpg','wb')
f.write(data)

