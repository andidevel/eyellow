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

import time
import threading
import queue
import json
import socket
import socketserver
import base64

import picamera

import RPi.GPIO as GPIO

from lib import (
    osutil,
    model,
)
from lib.socket_server import (
    StreamServer,
    BaseCommandProtocolHandler,
)


TURNED_ON_PIN = 5 # P29
SHUTDOWN_PIN = 12 # P32
DCIM_PATH = '/home/pi/DCIM'

camera = picamera.PiCamera()

class CommandHandler(BaseCommandProtocolHandler):

    def process_data(self, data):
        response = {
            'error': ''
        }
        try:
            data_json = json.loads(data)
            if data_json.get('connect') == 'close' and not self.connected:
                print('Closing connection...')
                self.close()
            else:
                print('Received:', data)
                db = model.DBModel()
                sample_id = db.insert_sample(data)
                sample_file = '{}/eye-sample-{}.jpg'.format(DCIM_PATH, sample_id)
                print('Capturing Image to file ', sample_file)
                camera.capture(sample_file, splitter_port=3, resize=(1920, 1080))
                # camera.capture(sample_file, splitter_port=3, resize=(3280, 1080))
                # camera.capture(sample_file, use_video_port=True)
                response['sample_id'] = sample_id
                response['sample_file'] = sample_file
                db.close()
                # Open the file, b64 encode and send
                with open(sample_file, 'rb') as fp:
                    fbytes = fp.read()
                # To b64
                fb64 = base64.b64encode(fbytes)
                # To response
                response['sample_file_content'] = fb64.decode('utf-8')
        except Exception as e:
            response['error'] = str(e)
            print('Error:\n\n', e)
        self.send_data(json.dumps(response, ensure_ascii=False))


def setup_shutdown_button(stream_server):
    def button_shutdown_pressed(channel):
        if channel == SHUTDOWN_PIN:
            stream_server.alive.clear()
            # Wait StreamServer thread ends
            time.sleep(1)
            # Shutdown device
            print('|----->[ SHUTING DOWN ]<-----|')
            osutil.shutdown()
    return button_shutdown_pressed


def init_hw(stream_server):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TURNED_ON_PIN, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # Button event
    GPIO.add_event_detect(SHUTDOWN_PIN, GPIO.RISING, callback=setup_shutdown_button(stream_server))


# self.camera.capture(sample_file, splitter_port=3, resize=(3280, 1080))


if __name__ == '__main__':
    stream_server = StreamServer(camera=camera)
    stream_server.daemon = True
    init_hw(stream_server)
    # Initialize Database
    db = model.DBModel()
    db.create_database()
    db.close()
    del db
    # Starts streaming
    stream_server.start()
    # Before start forever, turn on ready LED
    GPIO.output(TURNED_ON_PIN, GPIO.HIGH)
    print('Start Listening on 0.0.0.0:8080...')
    try:
        cmd_server = socketserver.TCPServer(('0.0.0.0', 8080), CommandHandler)
        cmd_server.serve_forever()
    finally:
        cmd_server.server_close()
        stream_server.alive.clear()
        # waiting close all
        time.sleep(1)
        GPIO.output(TURNED_ON_PIN, GPIO.LOW)
