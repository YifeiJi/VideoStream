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
        self.total = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(self.fps)

    def get_length(self):
        return self.total

    def next_frame(self):
        self.frame_number = self.frame_number + 1
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret == True:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return None
                cv2.imwrite('temp.jpg', frame)
                f = open('temp.jpg','rb')
                return f.read(), self.frame_number - 1
            else:
                return None


    def set_frame(self, pos):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        self.frame_number = pos
        return



