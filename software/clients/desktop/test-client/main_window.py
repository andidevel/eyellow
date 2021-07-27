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

import threading
import socket
import time
import struct
import io
import base64
import json
import datetime
import os

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import (
    GObject,
    GLib,
    Gtk,
    Gdk,
    GdkPixbuf
)

import cv2

import dip

from acquire_window import AcquireWindow
from model import LocalDBModel


class CaptureClient(threading.Thread):

    def __init__(self, host='localhost', port=2323, img_ctx=None):
        super(CaptureClient, self).__init__()
        self.host = host
        self.port = port
        self.img_ctx = img_ctx
        self.alive = threading.Event()
        self.alive.set()

    def run(self):
        client = socket.socket()
        client.connect((self.host, self.port))
        stream = client.makefile('rb')
        try:
            while self.alive.is_set():
                img_len = struct.unpack('<L', stream.read(struct.calcsize('<L')))[0]
                if not img_len:
                    # Connection closed
                    print('[StreamCapture] Zero length detected!')
                    break
                img_stream = io.BytesIO()
                img_stream.write(stream.read(img_len))
                img_stream.seek(0)
                jpg_img = GdkPixbuf.PixbufLoader.new_with_type('jpeg')
                jpg_img.write(img_stream.read())
                jpg_img.close()
                # self.img_ctx.set_from_pixbuf(jpg_img.get_pixbuf())
                GLib.idle_add(self.img_ctx.set_from_pixbuf, jpg_img.get_pixbuf())
        finally:
            stream.close()
            client.close()


class MainWindow(object):

    def __init__(self, application, vars=None):
        self.application = application
        self.vars = vars
        self.stream_connected = False
        self.terminator = '\r\n\r\n'
        try:
            self.builder = Gtk.Builder.new_from_file('test-client-form.glade')
            self.builder.connect_signals(self)
        except GObject.GError:
            print('MainWindow:: Error reading GUI file')
            raise
        self.capture_thread = CaptureClient(host=self.vars.server_host, img_ctx=self.builder.get_object('view_img'))
        self.capture_thread.daemon = True
        self.main_window = self.builder.get_object('main_window')
        self.main_window.set_application(self.application)
        self.main_window.show_all()

    def _readall(self, sock):
        data_in = ''
        read = sock.recv(4096)
        data_in += read.decode('utf-8')
        # Timeout: 2 seconds
        timeout = 2
        ti = datetime.datetime.now()
        timedout = False
        while (not data_in.find(self.terminator) > -1) and (not timedout):
            read = sock.recv(4096)
            data_in += read.decode('utf-8')
            timedout = (datetime.datetime.now() - ti).seconds > timeout
        return data_in[:data_in.find(self.terminator)]

    def _post(self, data):
        # Data to send is base64 encoded
        json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        data_b64 = base64.b64encode(json_bytes) + bytes(self.terminator, 'utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((self.vars.server_host, 8080))
            print('Sending data:', data_b64)
            client.sendall(data_b64)
            print('Receiving response...')
            data_b64 = self._readall(client)
            response_data = base64.b64decode(data_b64).decode('utf-8')
            print('Done.')
        return response_data

    def _get_radio_value(self, rd_ids):
        for rd_id, rd_value in rd_ids:
            if self.builder.get_object(rd_id).get_active():
                return rd_value

    def close(self, *args):
        self.capture_thread.alive.clear()
        # Wait finish connections
        time.sleep(1)
        self.main_window.destroy()

    def _on_btconnect_click(self, widget):
            self.capture_thread.start()
            self.stream_connected = True

    def _on_btshot_click(self, widget):
        if self.stream_connected:
            # Build the JSON message
            sample_data = {
                'age': 0,
                'height': 0.0,
                'weight':0.0,
                'diabetic_duration': '',
                'is_diabetic': self._get_radio_value(
                    (
                        ('rd_diabetic_no', 0),
                        ('rd_diabetic_yes', 1),
                        ('rd_diabetic_pre', 2)
                    )
                ),
                'dm_type': self._get_radio_value((('rd_dm_type0', 0), ('rd_dm_type1', 1), ('rd_dm_type2', 2))),
                'has_DR': self._get_radio_value((('rd_dr_no', 0), ('rd_dr_yes', 1))),
                'has_DNP': self._get_radio_value((('rd_dnp_no', 0), ('rd_dnp_yes', 1))),
                'has_DNR': self._get_radio_value((('rd_dnr_no', 0), ('rd_dnr_yes', 1))),
                'has_CDN': self._get_radio_value((('rd_cdn_no', 0), ('rd_cdn_yes', 1))),
                'gender': self._get_radio_value((('rd_gender_man', 0), ('rd_gender_woman', 1)))
            }
            if self.builder.get_object('ed_age').get_text():
                sample_data['age'] = int(self.builder.get_object('ed_age').get_text())
            if self.builder.get_object('ed_duration').get_text():
                sample_data['diabetic_duration'] = self.builder.get_object('ed_duration').get_text()
            text_entry = self.builder.get_object('ed_height').get_text()
            if text_entry:
                text_entry = text_entry.replace(',', '.')
                sample_data['height'] = float(text_entry)
            text_entry = self.builder.get_object('ed_weight').get_text()
            if text_entry:
                text_entry = text_entry.replace(',', '.')
                sample_data['weight'] = float(text_entry)
            # TODO: Validade age, height and weight
            response = self._post(sample_data)
            # Wait for response
            if response:
                resp_obj = json.loads(response)
                sample_data['remote_sample_file'] = resp_obj.get('sample_file')
                # Saving locally
                self.vars.last_sample_id = self.vars.db.insert_sample(resp_obj['sample_id'], json.dumps(sample_data, ensure_ascii=False))
                # Now decode the picture, slice and show
                fcontent = base64.b64decode(resp_obj['sample_file_content'])
                fname = os.path.basename(sample_data['remote_sample_file'])
                flocal_name = '/'.join([self.vars.app_dir, 'imgs', fname])
                with open(flocal_name, 'wb') as fp:
                    fp.write(fcontent)
                # Reopen image as OpenCV matrix
                sample_img_bgr = cv2.imread(flocal_name)
                # Slice image
                self.vars.sample_img_bgr = dip.crop_img(sample_img_bgr)
                AcquireWindow(self.application, vars=self.vars)
        else:
            # Test
            print('Loading test imaging...')
            # TODO: Get these informations via .env parameters
            sample_img_bgr = cv2.imread('../data/imgs/eye-sample-2.jpg')
            # Slice image
            self.vars.sample_img_bgr = dip.crop_img(sample_img_bgr)
            # Test ID
            self.vars.last_sample_id = 1
            AcquireWindow(self.application, vars=self.vars)
        # print(sample_data)
