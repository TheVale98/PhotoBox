#!/usr/bin/env python

import sys
import io

from devices.camera import Camera
import time
import cv2
import numpy as np
import gphoto2 as gp
import PhotoBooth as pb
from utils.config import Config
from trigger import TriggerThread

from PySide2.QtWidgets import QApplication, QMainWindow, QWidget
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtCore import QThread, Qt, QObject, Signal, Slot

config = Config()

class PhotoBooth(QMainWindow, pb.Ui_PhotoBooth):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.cameraThread = CameraThread()
        self.cameraThread.newImage.connect(self.newImageDetected)
        self.triggerThread = TriggerThread(config.get_serial_port())
        self.triggerThread.trigger.connect(self.takePicture)
        self.cameraThread.start()
        self.triggerThread.start() 
        self.pushButton.clicked.connect(self.takePicture)
        self.pixmap = None
        if config.get_debug() == "False":
            self.pushButton.hide()

        self.showFullScreen()    

    def resizeEvent(self, event):
        if not self.pixmap is None:
            self.label.setPixmap(self.pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))

        QWidget.resizeEvent(self, event)

    def takePicture(self, test):
        self.cameraThread.trigger = True
        print("set property")



    def closeEvent(self, event):
        self.cameraThread.__del__()
        event.accept()


    def newImageDetected(self, img):
        self.pixmap = QPixmap(img)
        self.label.setPixmap(self.pixmap.scaled(self.label.width(), self.label.height()))

class CameraThread(QThread):
    newImage = Signal(QImage)
    def __init__(self):
        QThread.__init__(self)
        print("Starting tread")
        self.run_thread = True
        self.trigger = False
        self.camera = Camera()
        print("init done ")

    def __del__(self):
        print("closing thread") 
        self.run_thread = False
        self.camera.disconnect_camera()
        self.wait()

    def run(self): 
        print("starting preview")
            
        while self.run_thread:
            # capturing preview and sending it to ui
            img = self.camera.capture_next_preview_as_np_array()
            self.newImage.emit(self._convert_picture_to_qimage(img))

            if self.trigger == True:
                cap_img =  self.camera.capture_image()
                saved_picture = self.camera.save_image(config.get_output_path(), cap_img)
                pixmap = QPixmap(saved_picture)
                
                self.newImage.emit(pixmap.toImage())
                self.sleep(config.get_image_show_time_in_s())
                self.trigger = False
        
        time.sleep(1)
        print("deleting camera")

    def _convert_picture_to_qimage(self, img):
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        height, width, channels = img.shape
        res = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return QImage(res, width, height, width*channels, QImage.Format_RGB888)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pb = PhotoBooth()
    pb.show()
    sys.exit(app.exec_())
