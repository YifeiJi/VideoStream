import subprocess
import os
import ffmpeg
import math


def make_cache(file_name, cache_path):
    print("Preprocess video: " + file_name)
    real_name = file_name
    real_name = real_name.split('.')[0]
    audio_name = real_name + '.mp3'
    info = ffmpeg.probe(file_name)
    stream = info['streams']
    #print(stream)
    sec = math.ceil(float(stream[0]['duration']))

    cmd_img_low = 'ffmpeg -i ' + file_name + ' -qscale:v 31 ' + cache_path + '\%d-low.jpg -v quiet'
    subprocess.call(cmd_img_low, shell=True)
    cmd_img = 'ffmpeg -i ' + file_name + ' -qscale:v 10 ' + cache_path + '\%d.jpg -v quiet'
    print(cmd_img)
    subprocess.call(cmd_img, shell=True)

    audio_path = os.path.join(cache_path,audio_name)
    cmd = 'ffmpeg -i ' + file_name + ' -f mp3 ' + audio_path + ' -v quiet'
    print(cmd)
    subprocess.call(cmd, shell=True)

    for i in range(0, sec):
        cmd = 'ffmpeg -i %s -ss %d -t 1.1 -codec copy %s_%d.mp3 -hide_banner -v quiet' % \
              (audio_path, i, os.path.join(cache_path, real_name), i)
        subprocess.call(cmd, shell=True)

    print("Preprocess Done: " + file_name)
    print('----------')


