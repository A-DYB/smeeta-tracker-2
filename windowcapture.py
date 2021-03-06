import numpy as np
import win32api, win32con, win32gui, win32ui
from win32api import GetSystemMetrics

class WindowCapture:
    hwnd = None
    window_name = None
    cropped_x = cropped_y = 0

    # constructor
    def __init__(self, window_name, capture_size, ui):
        self.ui = ui
        self.window_name = window_name
        # find the handle for the window we want to capture
        self.hwnd = win32gui.FindWindow(None, self.window_name)
        self.w, self.h = capture_size
        if not self.hwnd:
            #raise Exception('Window not found: {}'.format(window_name))
            print('Window not found: {}'.format(window_name))
            self.ui.window_capture_status_label.setText("Warframe window not found")
        else:
            self.ui.window_capture_status_label.setText("Warframe window found!")

    def get_screenshot(self, avg_width=None):
        #get window properties
        if not self.hwnd:
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            if self.hwnd:
                self.ui.window_capture_status_label.setText("Warframe window found!")
            else:
                return None
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
        except:
            self.ui.window_capture_status_label.setText("Warframe window not found")
            self.hwnd = win32gui.FindWindow(None, self.window_name)
            if self.hwnd:
                self.ui.window_capture_status_label.setText("Warframe window found!")
            return None
        win_w = rect[2] - rect[0]
        # y_border_thickness = GetSystemMetrics(33) + GetSystemMetrics(4)
        y_border_thickness = 0

        #Upper left corner of detection box, given top left of screen is 0,0
        self.cropped_x, self.cropped_y  = ( int(win_w - self.w ) , int(y_border_thickness) )

        # get the window image data
        try:
            wDC = win32gui.GetWindowDC(self.hwnd)
        except:
            raise Exception('Window not found: {}'.format(self.window_name))

        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() 
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img
