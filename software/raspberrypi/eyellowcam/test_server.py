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

import socketserver
import base64
import json

from lib import model
from lib.socket_server import BaseCommandProtocolHandler


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
                db = model.DBModel('.')
                sample_id = db.insert_sample(data)
                sample_file = 'eye-sample-{}.jpg'.format(sample_id)
                print('Capturing Image to file ', sample_file)
                # camera.capture(sample_file, splitter_port=3, resize=(3280, 1080))
                response['sample_id'] = sample_id
                response['sample_file'] = sample_file
                db.close()
        except Exception as e:
            response['error'] = str(e)
            print('Error:\n\n', e)
        self.send_data(json.dumps(response, ensure_ascii=False))


if __name__ == '__main__':
    print('Creating Database...')
    db = model.DBModel('.')
    db.create_database()
    db.close()
    print('Start Listening on localhost:8080...')
    with socketserver.TCPServer(('localhost', 8080), CommandHandler) as server:
        server.serve_forever()
    