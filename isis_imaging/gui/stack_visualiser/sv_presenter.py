from __future__ import absolute_import, division, print_function

import os
from enum import IntEnum

from isis_imaging.core.io import Images
from isis_imaging.gui.stack_visualiser.sv_model import \
    ImgpyStackVisualiserModel


class Notification(IntEnum):
    RENAME_WINDOW = 0
    HISTOGRAM = 1
    NEW_WINDOW_HISTOGRAM = 2


class StackViewerPresenter(object):
    def __init__(self, view, images: Images, axis):
        super(StackViewerPresenter, self).__init__()
        self.view = view
        self.images = images
        self.axis = axis

        self.model = ImgpyStackVisualiserModel()

    def notify(self, signal):
        try:
            if signal == Notification.RENAME_WINDOW:
                self.do_rename_view()
            elif signal == Notification.HISTOGRAM:
                self.do_histogram()
            elif signal == Notification.NEW_WINDOW_HISTOGRAM:
                self.do_new_window_histogram()
        except Exception as e:
            self.show_error(e)
            raise  # re-raise for full stack trace

    def show_error(self, error):
        print("Magic to be done here")

    def do_rename_view(self):
        self.view.update_title_event()

    def do_histogram(self):
        self.view.show_histogram_of_current_image(new_window=False)

    def do_new_window_histogram(self):
        self.view.show_histogram_of_current_image(new_window=True)

    def delete_data(self):
        del self.images

    def get_image(self, index):
        if self.axis == 0:
            return self.images.get_sample()[index, :, :]
        elif self.axis == 1:
            return self.images.get_sample()[:, index, :]
        elif self.axis == 2:
            return self.images.get_sample()[:, :, index]

    def get_image_fullpath(self, index):
        return self.images.get_filenames()[index]

    def get_image_filename(self, index):
        return os.path.basename(self.images.get_filenames()[index])

    def apply_to_data(self, func, *args, **kwargs):
        # TODO refactor, and provide a way to read ROI
        # TODO provide a standard way to request parameters?
        # TODO Should we go to Mantid-style algorithm with functions like getProperty, etc?
        # It might be worth moving back into mantid at that point and using the existing algorithm structure
        do_before = getattr(func, "do_before", None)
        if do_before:
            delattr(func, "do_before")
        do_after = getattr(func, "do_after", None)
        if do_after:
            delattr(func, "do_after")

        if do_before:
            res_before = do_before(self.images.get_sample())
        func(self.images.get_sample(), *args, **kwargs)
        if do_after:
            do_after(self.images.get_sample(), res_before)
        self.view.show_current_image()
