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

import base64
import math
import json

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

import numpy as np

import dip

from model import LocalDBModel


class AcquireWindow(object):

    def __init__(self, application, vars=None):
        self.application = application
        self.vars = vars
        self.eye_side = 'R'
        self._reset_image_actions()
        try:
            self.builder = Gtk.Builder.new_from_file('acquire_window.glade')
            self.builder.connect_signals(self)
        except GObject.GError:
            print('AcquireWindow:: Error reading GUI file')
            raise
        self.acquire_window = self.builder.get_object('acquire_window')
        self.acquire_window.set_application(self.application)
        # Init image preview
        dip.show_img(self.builder.get_object('img_preview'), self.vars.sample_img_bgr)
        self._change_eye()
        self.acquire_window.show_all()

    def close(self, *args):
        self.acquire_window.destroy()

    def _reset_image_actions(self):
        self.im_filtered = None
        self.gb_mask = None
        self.gb_fg_model = None
        self.gb_bg_model = None
        self.gb_im_mask = None
        self.gb_mask_aux = None
        self.start_drawing = False
        self.drawing_type = 0
        self.rect_x1 = 0
        self.rect_y1 = 0
        self.rect_x2 = 0
        self.rect_y2 = 0
        self.gb_final_mask = None

    def _change_eye(self):
        if self.eye_side == 'R':
            self.im_filtered = dip.right_eye(self.vars.sample_img_bgr)
        else:
            self.im_filtered = dip.left_eye(self.vars.sample_img_bgr)
        self.im_filtered = cv2.bilateralFilter(self.im_filtered, 9, 75, 75)
        dip.show_img(self.builder.get_object('work_img'), self.im_filtered)
        self._label_eye_side()

    def _label_eye_side(self):
        if self.eye_side == 'R':
            self.builder.get_object('lb_working_eye').set_text('Olho Direito')
        else:
            self.builder.get_object('lb_working_eye').set_text('Olho Esquerdo')

    def _get_drawing_type(self):
        radios = (('rd_rect', 0), ('rd_foreground', 1), ('rd_background', 2))
        for rd, dt in radios:
            if self.builder.get_object(rd).get_active():
                return dt
        return 0

    def _draw_fg_bg_pixel(self, x, y):
        bgr = [255, 255, 255]
        mask_point = 1
        if self.drawing_type == 2:
            bgr = [0, 0, 0]
            mask_point = 0
        x1a, x1b = x, x
        y1a, y1b = y, y
        if x > 1:
            x1a -= 1
        if x < (self.gb_im_mask.shape[1]-1):
            x1b += 1
        if y > 1:
            y1a -= 1
        if y < (self.gb_im_mask.shape[0]-1):
            y1b += 1
        self.gb_im_mask[y1a:y1b, x1a:x1b] = bgr
        self.gb_mask_aux[y1a:y1b, x1a:x1b] = mask_point
        dip.show_img(self.builder.get_object('work_img'), self.gb_im_mask)

    def _on_work_img_button_press(self, widget, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == 1:
                self.start_drawing = True
                self.rect_x1 = math.floor(event.x)
                self.rect_y1 = math.floor(event.y)
                if self.drawing_type in (1, 2) and self.gb_im_mask is None:
                    self.gb_im_mask = self.im_filtered.copy()
                    self.gb_mask_aux = self.gb_mask.copy()
                    self._draw_fg_bg_pixel(self.rect_x1, self.rect_y1)
        return True

    def _on_work_img_motion(self, widget, event):
        if self.start_drawing:
            x2 = math.floor(event.x)
            y2 = math.floor(event.y)
            if self.drawing_type == 0:
                if x2 >= self.rect_x1 and y2 >= self.rect_y2:
                    im_rect = cv2.rectangle(self.im_filtered.copy(), (self.rect_x1, self.rect_y1), (x2, y2), (255, 0, 0), 2)
                    dip.show_img(self.builder.get_object('work_img'), im_rect)
            else:
                self._draw_fg_bg_pixel(x2, y2)
        return True

    def _on_work_img_button_release(self, widget, event):
        if self.start_drawing:
            self.start_drawing = False
        self.rect_x2 = math.floor(event.x)
        self.rect_y2 = math.floor(event.y)
        return True

    def _on_rd_toggle(self, widget):
        self.drawing_type = self._get_drawing_type()

    def _on_btapply_click(self, widget):
        if self.drawing_type == 0:
            self.gb_mask, self.gb_bg_model, self.gb_fg_model = dip.grab_cut_rect(
                self.im_filtered,
                (self.rect_x1, self.rect_y1, self.rect_x2, self.rect_y2)
            )
            im_mask = np.where((self.gb_mask==2)|(self.gb_mask==0), 0, 1).astype('uint8')
            im_masked = self.im_filtered * im_mask[:, :, np.newaxis]
            dip.show_img(self.builder.get_object('result_img'), im_masked)
        if self.drawing_type in (1, 2):
            if self.gb_bg_model is not None and self.gb_fg_model is not None and self.gb_mask_aux is not None:
                gb_mask, self.gb_bg_model, self.gb_fg_model = dip.grab_cut_mask(
                    self.im_filtered,
                    self.gb_mask_aux,
                    bg_model=self.gb_bg_model,
                    fg_model=self.gb_fg_model
                )
                self.gb_final_mask = np.where((gb_mask==2)|(gb_mask==0), 0, 1).astype('uint8')
                im_masked = self.im_filtered * self.gb_final_mask[:, :, np.newaxis]
                # Save masked image
                fmask = '/'.join([self.vars.app_dir, 'imgs', 'gb_masked.jpg'])
                print('Saving to ', fmask)
                cv2.imwrite(fmask, im_masked)
                dip.show_img(self.builder.get_object('result_img'), im_masked)

    def _on_btreset_work_img(self, widget):
        self._reset_image_actions()
        self._change_eye()

    def _on_btfeature_click(self, widget):
        # print(self.gb_final_mask)
        if self.gb_final_mask is not None:
            bgr_mean_vector, br_value, bg_value = dip.calc_yellow(self.gb_final_mask, self.im_filtered)
            self.builder.get_object('lb_br_value').set_text('{:.2f}'.format(br_value))
            self.builder.get_object('lb_bg_value').set_text('{:.2f}'.format(bg_value))
            # Updating sample
            sample_row = self.vars.db.get_sample(self.vars.last_sample_id)
            # Sample data is 4th col
            sample_data = json.loads(sample_row[3])
            if not ('eyes' in sample_data):
                sample_data['eyes'] = {}
            sample_data['eyes'][self.eye_side] = {
                'BR': float(br_value),
                'BG': float(bg_value),
                'BGR': [i for i in map(int, bgr_mean_vector)]
            }
            # Convert to JSON
            sample_json = json.dumps(sample_data, ensure_ascii=False)
            self.vars.db.update_sample(self.vars.last_sample_id, sample_json)

    def _on_btchange_eye_click(self, widget):
        if self.eye_side == 'R':
            self.eye_side = 'L'
        else:
            self.eye_side = 'R'
        self._reset_image_actions()
        self._change_eye()
