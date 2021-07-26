# MIT License

# Copyright (c) 2021 Anderson R. Livramento

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import socket
import socketserver
import threading
import io
import struct
import base64
import datetime


####################[ Stream Server ]#################################################
# Camera Streamming, most of code based on
# https://picamera.readthedocs.io/en/latest/recipes2.html#rapid-capture-and-streaming

class SplitFrames(object):

    def __init__(self, conn):
        self.conn = conn
        self.stream = io.BytesIO()

    def write(self, buffer):
        if buffer.startswith(b'\xff\xd8'):
            # Start of new frame;
            size = self.stream.tell()
            if size > 0:
                self.conn.write(struct.pack('<L', size))
                self.conn.flush()
                self.stream.seek(0)
                self.conn.write(self.stream.read(size))
                self.stream.seek(0)
        self.stream.write(buffer)


class StreamServer(threading.Thread):

    def __init__(self, camera, port=2323):
        super(StreamServer, self).__init__()
        self.camera = camera
        self.camera.resolution = 'VGA'
        self.camera.framerate = 30
        self.port = port
        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        server = socket.socket()
        server.bind(('0.0.0.0', self.port))
        server.listen(0)
        while self.alive.is_set():
            print('\n[StreamServer] Waiting for connection...')
            conn, addr = server.accept()
            stream = conn.makefile('wb')
            output = SplitFrames(stream)
            print('\n[StreamServer] Connected to: ', addr)
            try:
                self.camera.start_recording(output, format='mjpeg')
                while self.alive.is_set():
                    try:
                        self.camera.wait_recording()
                    except Exception:
                        break
                self.camera.stop_recording()
                stream.close()
            except Exception as e:
                print('\n[StreamServer] ERROR: ', e)
            finally:
                conn.close()
                print('\n[StreamServer] Connection closed.')
        server.close()

####################[ Command Server ]#############################################
class BaseCommandProtocolHandler(socketserver.BaseRequestHandler):
    terminator = '\r\n\r\n'

    def readall(self):
        data_in = ''
        read = self.request.recv(4096)
        data_in += read.decode('utf-8')
        # Timeout: 2 seconds
        timeout = 2 
        ti = datetime.datetime.now()
        timedout = False
        while (not data_in.find(self.terminator) > -1) and (not timedout):
            read = self.request.recv(4096)
            data_in += read.decode('utf-8')
            timedout = (datetime.datetime.now() - ti).seconds > timeout
        return data_in[:data_in.find(self.terminator)]
    
    def send_data(self, data):
        data_b64 = base64.b64encode(bytes(data, 'utf-8')) + bytes(self.terminator, 'utf-8')
        self.request.sendall(data_b64)

    def handle(self):
        data_b64 = self.readall()
        data = base64.b64decode(data_b64)
        self.process_data(data.decode('utf-8'))
    
    def process_data(self, data):
        raise NotImplementedError
