# -*- coding:utf-8 -*-
import time
from PySide6.QtCore import Qt, QThread, Signal, QDateTime,QMutex,QWaitCondition as QWC
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QApplication, QLabel, QLineEdit,
                               QSlider, QPushButton, QGridLayout,
                               QDateTimeEdit)


class Timer(QThread):
    '''
    buyTime:字符串时间
    sleepInterval:时钟
    advance:提前量(s)
    '''
    # just a try
    infoSignal = Signal(datetime)
    stopFlag=False
    sleepMutex=QMutex()
    sleepMutex.lock()
    def Sleep(self,time):
        self.sleepMutex.tryLock(time*1000)
    # just a try
    def __init__(self,
                 buyTime,
                 sleepInterval=0.05,
                 advance=0,
                 auto_interval_on=False,
                 averJDMinusSystem=timedelta(seconds=0)):
        super().__init__()
        self.auto_interval_on = auto_interval_on
        self.averJDMinusSystem = averJDMinusSystem
        self.advance = timedelta(seconds=advance)
        self.buy_time = datetime.strptime(buyTime, "%Y-%m-%d %H:%M:%S")
        self.sleepInterval = sleepInterval

    def run(self):
        self.stopFlag=False
        now_time = lambda: datetime.now() + (self.averJDMinusSystem
                                             if self.auto_interval_on == True
                                             else timedelta(seconds=0))
        while not self.stopFlag:
            if now_time() >= self.buy_time - self.advance:
                break
            else:
                self.Sleep(self.sleepInterval)
            # print("emit {0}".format(now_time()))
            self.infoSignal.emit(now_time())
    def stop(self):
        if(self.stopFlag):
            return
        self.stopFlag=True
        self.sleepMutex.unlock()
        self.quit()
        self.wait()
        print("Timer stopped")