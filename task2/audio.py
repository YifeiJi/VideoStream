import wave
import pyaudio
import subprocess
CHUNK = 1024

# def play(filename = 'a.wav'):
#     wf = wave.open(filename, 'rb')
#     p = pyaudio.PyAudio()
#     print(p.get_format_from_width(wf.getsampwidth()))
#     stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
#                     channels=wf.getnchannels(),
#                     rate=wf.getframerate(),
#                     output=True)
#     data = wf.readframes(CHUNK)
#     while data != b'':
#         stream.write(data)
#         data = wf.readframes(CHUNK)
#
#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     return

# play()
from playsound import playsound

subprocess.call(playsound('a.mp3'))

