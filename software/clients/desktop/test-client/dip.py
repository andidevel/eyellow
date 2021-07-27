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

import cv2

import numpy as np

from gi.repository import GdkPixbuf

CROP_RECT = (125, 325, 1700, 725)
CENTER_OFFSET = 250
TOP_OFFSET = 150
BOTTOM_OFFSET = 380
LEFT_OFFSET = 80
RIGHT_OFFSET = 1494

def crop_img(image):
    return image[CROP_RECT[1]:CROP_RECT[3], CROP_RECT[0]:CROP_RECT[2]].copy()


def cv_to_pixbuf(cvimg, to_color=cv2.COLOR_BGR2RGB):
    rgb_image = cv2.cvtColor(cvimg, to_color)
    height, width, depth = rgb_image.shape
    try:
        pnm_img = GdkPixbuf.PixbufLoader.new_with_type('pnm')
        header = 'P6 {} {} 255\n'.format(width, height)
        pnm_img.write(bytes(header, encoding='utf-8'))
        pnm_img.write(rgb_image.tostring())
    finally:
        pnm_img.close()
    return pnm_img.get_pixbuf()


def show_img(gtkimage, cvimage, to_color=cv2.COLOR_BGR2RGB):
    # allocation = gtkimage.get_allocation()
    allocation = gtkimage.get_size_request()
    # request_size = gtkimage.get_size_request()
    gtk_width, gtk_height = (allocation.width, allocation.height)
    # print('GtkImage(w={}, h={})'.format(gtk_width, gtk_height))
    # print('Requested Size: ', request_size)
    # print('CVImage(w={}, h={})'.format(cvimage.shape[1], cvimage.shape[0]))
    if len(cvimage.shape) > 2:
        cv_height, cv_width, cv_depth = cvimage.shape
    else:
        cv_height, cv_width = cvimage.shape
    new_image = cvimage
    can_resize = False
    if cv_height > gtk_height:
        can_resize = True
    else:
        gtk_height = cv_height
    if cv_width > gtk_width:
        can_resize = True
    else:
        gtk_width = cv_width
    if can_resize:
        new_image = cv2.resize(cvimage, (gtk_width, gtk_height), interpolation=cv2.INTER_AREA)
    pixbuf = cv_to_pixbuf(new_image, to_color=to_color)
    gtkimage.set_from_pixbuf(pixbuf)


def grab_cut_rect(image, rect, ite=5, bg_model=None, fg_model=None):
    mask = np.zeros(image.shape[:2], np.uint8)
    if bg_model is None:
        bg_model = np.zeros((1, 65), np.float64)
    if fg_model is None:
        fg_model = np.zeros((1, 65), np.float64)
    # rect = (ix, iy, fx, fy) -> w = abs(ix-fx) ; h = abs(iy-fy)
    gc_rect = (rect[0], rect[1], abs(rect[0]-rect[2]), abs(rect[1]-rect[3]))
    cv2.grabCut(image, mask, gc_rect, bg_model, fg_model, ite, cv2.GC_INIT_WITH_RECT)
    return (mask, bg_model, fg_model)


def grab_cut_mask(image, mask, bg_model, fg_model, ite=5):
    if bg_model is None:
        bg_model = np.zeros((1, 65), np.float64)
    if fg_model is None:
        fg_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, mask, None, bg_model, fg_model, ite, cv2.GC_INIT_WITH_MASK)
    return (mask, bg_model, fg_model)


def right_eye(img_croped):
    half = img_croped.shape[1] // 2
    return img_croped[TOP_OFFSET:BOTTOM_OFFSET, LEFT_OFFSET:(half-CENTER_OFFSET)].copy()


def left_eye(img_croped):
    half = img_croped.shape[1] // 2
    return img_croped[TOP_OFFSET:BOTTOM_OFFSET, (half+CENTER_OFFSET):RIGHT_OFFSET].copy()

def calc_yellow(gb_mask, image):
    if gb_mask is not None:
        bgr_mask_pixels = image[gb_mask==1]
        bgr_mean_vector = np.mean(bgr_mask_pixels, axis=0).astype('uint8')
        br_value = bgr_mean_vector[0]/bgr_mean_vector[2]
        bg_value = bgr_mean_vector[0]/bgr_mean_vector[1]
        return (bgr_mean_vector, br_value, bg_value)
    return None
