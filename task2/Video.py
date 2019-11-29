import ffmpeg
import os
import subprocess

class _Video:
    def __init__(self, filename):
        self.file = filename
        self.info = ffmpeg.probe(filename)
        self.stream = self.info['streams']
        self.total_frames = int(self.stream[0]['nb_frames'])
        self.frame_to_play = 1
        fps = self.stream[0]['r_frame_rate'].split('/')
        self.fps = int(int(fps[0])/int(fps[1]))


    def get_length(self):
        return self.total_frames

    def next_frame(self):
        if self.frame_to_play > self.total_frames:
            return None
        out = self.read_frame(self.frame_to_play)
        self.frame_to_play = self.frame_to_play + 1
        return out, self.frame_to_play - 1

    def set_frame(self, pos):
        self.frame_to_play = pos

    def read_frame(self, frame_num):
        #print('frame_num',frame_num)
        sec = frame_num // self.fps + 1
        index = frame_num % self.fps
        if index == 0:
            index = self.fps
        if index == self.fps:
            sec = sec - 1
        name = 'cache-' + str(sec) + '-' + str(index).zfill(4) + '.jpg'
        if index == 1:
            cmd = 'ffmpeg -i ' + self.file + ' -ss ' + str(sec) + ' -vframes ' + str(self.fps) + ' cache-' + str(sec) + '-' + '%04d.jpg -v quiet'
            subprocess.call(cmd, shell=True)
        # out, err = (
        #     ffmpeg
        #     .input(self.file)
        #     .filter('select', 'gte(n,{})'.format(frame_num))
        #     .output('pipe:', vframes=1, format='image2', vcodec='mjpeg')
        #     .run(quiet=True, capture_stdout=True)
        # )
        #print(name)
        f = open(name,'rb')
        out = f.read()
        #print(out)
        return out
#
import cv2



class  Video:
    def __init__(self,filename):
        self.filename = filename
        self.frame_number = 0
        self.file = open(filename,'rb')
        self.cap = cv2.VideoCapture(filename)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))

        self.audio = self.filename
        self.audio.split('.')
        self.audio = self.audio[0] + '.' + 'mp3'
        self.base_cache = 'server-cache'
        if not os.path.exists(self.base_cache):
            os.makedirs(self.base_cache)
        print(self.audio)
        self.sec = self.total // self.fps + 1
        if self.total % self.fps == 0:
            self.sec = self.sec - 1
        self.sec = int(self.sec)
        self.source_audio = os.path.join(self.base_cache, self.audio)
        if not os.path.exists(self.source_audio):
            cmd = 'ffmpeg -i ' + self.filename + ' -f mp3 ' + self.source_audio
            print(cmd)
            subprocess.call(cmd, shell=True)

            real_name = self.audio
            real_name = real_name.replace('.mp3','')
            print(self.sec)

            for i in range(0, self.sec):

                cmd = 'ffmpeg -i %s -ss %d -t 1 -codec copy %s_%d.mp3 -hide_banner -v quiet' % (self.source_audio, i, os.path.join(self.base_cache, real_name), i)
                subprocess.call(cmd, shell=True)


    def get_size(self):
        return self.height, self.width

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

# a = Video('a.mp4')
# out = a.next_frame()
# print(len(out[0]))