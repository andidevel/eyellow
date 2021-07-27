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

import os

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import (
    GLib,
    Gtk,
    Gdk,
    GdkPixbuf
)

from main_window import MainWindow
from model import LocalDBModel

class GlobalVars(object):
    server_host = 'localhost'
    app_dir = os.path.dirname(os.path.abspath(__file__))
    db = None


class MyApplication(Gtk.Application):

    def __init__(self, application_id, vars=None):
        Gtk.Application.__init__(self, application_id=application_id)
        self.vars = vars
        self.connect('activate', self.new_window)

    def new_window(self, *args):
        MainWindow(self, vars=self.vars)

if __name__ == '__main__':
    vars = GlobalVars()
    # TODO: Get these informations via .env parameters
    vars.server_host = '192.168.2.1'
    # Create the database
    vars.db = LocalDBModel(vars.app_dir)
    vars.db.create_database()
    app = MyApplication('com.catfishlabs.eyellowcam_client', vars=vars)
    app.run()
