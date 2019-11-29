import ffmpeg
import os
import subprocess
import math
import cv2



class  Video:
    def __init__(self,filename):
        self.filename = filename
        self.frame_to_play = 0
        self.audio = self.filename
        self.audio.split('.')
        self.audio = self.audio[0] + '.' + 'mp3'
        self.base_cache = os.path.join('server-cache',self.filename)

        self.info = ffmpeg.probe(self.filename)
        self.stream = self.info['streams']
        print(self.stream)
        self.sec = math.ceil(float(self.stream[0]['duration']))
        self.total = int(self.stream[0]['nb_frames'])
        self.height = int(self.stream[0]['height'])
        self.width = int(self.stream[0]['width'])

        self.fps = self.stream[0]['r_frame_rate']
        self.fps = self.fps.split('/')
        print(self.fps)
        self.fps = int(int(self.fps[0]) / int(self.fps[1]))
        print(self.fps)
        self.source_audio = os.path.join(self.base_cache, self.audio)


    def get_size(self):
        return self.height, self.width

    def get_length(self):
        return self.total

    def next_frame(self):
        self.frame_to_play = self.frame_to_play + 1
        if self.frame_to_play > self.total:
            return None
        file_path = os.path.join(self.base_cache,str(self.frame_to_play) + '.jpg')
        try:
            f = open(file_path, 'rb')
            return f.read(), self.frame_to_play - 1
        except:
            return None

    def set_frame(self, pos):
        self.frame_to_play = pos
        return

# a = Video('a.mp4')
# out = a.next_frame()
# print(len(out[0]))