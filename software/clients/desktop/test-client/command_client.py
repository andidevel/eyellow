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

import asyncore
import asynchat
import base64
import socket


class BaseCommandClient(asynchat.async_chat):

    def __init__(self, host='localhost', port=8080):
        super(BaseCommandClient, self).__init__()
        self.set_terminator('\r\n\r\n')
        self.data_in = []
        self.host = host
        self.port = port
    
    def start_connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Connecting to: {}:{}'.format(self.host, self.port))
        self.connect((self.host, self.port))
        asyncore.loop()
    
    def collect_incoming_data(self, data):
        self.data_in.append(data)
    
    def found_terminator(self):
        if self.data_in:
            data_b64 = ''.join(self.data_in)
            data = base64.b85decode(data_b64)
            self.data_received(data.decode('utf-8'))
        self.data_in = []
    
    def handle_connect(self):
        try:
            self.connection_made()
        except:
            self.close()
    
    def handle_close(self):
        self.close()
        self.connection_lost()
    
    def send_data(self, data):
        data_b64 = base64.b64encode(data)
        self.push(data_b64)
        self.push(self.get_terminator())
    
    def data_received(self, data):
        raise NotImplementedError

    def connection_made(self):
        raise NotImplementedError

    def connection_lost(self):
        pass
