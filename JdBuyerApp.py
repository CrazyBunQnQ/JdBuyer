# -*- coding:utf-8 -*-
import sys
import os
import time
import json
from log import logger
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QThread, Signal, QDateTime
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QWidget, QApplication, QLabel, QLineEdit,
                               QSlider, QPushButton, QGridLayout,
                               QDateTimeEdit)

from timer import Timer
from JdSession import Session
from JdTime import JDTime

NUM_LABEL_FORMAT = '商品购买数量[{0}]个'
STOCK_LABEL_FORMAT = '库存查询间隔[{0}]秒'
DATA_FORMAT = '%H:%M:%S'
auto_interval_on = False
jd_time_on =False
infotext = ["", ""]
averJDMinusSystem = timedelta(seconds=0.05)  #millisecond

if getattr(sys, 'frozen', False):
    absPath = os.path.dirname(os.path.abspath(sys.executable))
elif __file__:
    absPath = os.path.dirname(os.path.abspath(__file__))


class JdBuyerUI(QWidget):

    def __init__(self):
        super().__init__()
        self.session = Session()
        self.ticketThread = TicketThread(self.session)
        self.ticketThread.ticketSignal.connect(self.ticketSignal)
        self.initUI()
        self.loadData()

    def loadData(self):
        with open(os.path.join(absPath, 'config.json'), "rb") as f:
            self.config = json.load(f)
        self.skuEdit.setText(self.config.get('skuId'))
        self.areaEdit.setText(self.config.get('areaId'))
        self.passwordEdit.setText(self.config.get('password'))
        self.numSlider.setValue(self.config.get('count'))
        self.stockSlider.setValue(self.config.get('stockInterval'))
        self.numLabel.setText(NUM_LABEL_FORMAT.format(
            self.config.get('count')))
        self.stockLabel.setText(
            STOCK_LABEL_FORMAT.format(self.config.get('stockInterval')))

    def saveData(self):
        with open(os.path.join(absPath, 'config.json'), 'w',
                  encoding='utf-8') as f:
            # json.dump(my_list,f)
            # 直接显示中文,不以ASCII的方式显示
            # json.dump(my_list,f,ensure_ascii=False)
            # 显示缩进
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(10)

        # 商品SKU
        skuLabel = QLabel('商品SKU')
        self.skuEdit = QLineEdit()
        grid.addWidget(skuLabel, 1, 0)
        grid.addWidget(self.skuEdit, 1, 1)

        # 区域ID
        areaLabel = QLabel('地区ID')
        self.areaEdit = QLineEdit()
        grid.addWidget(areaLabel, 2, 0)
        grid.addWidget(self.areaEdit, 2, 1)

        # 购买数量
        self.numLabel = QLabel(NUM_LABEL_FORMAT.format(1))
        self.numSlider = QSlider(Qt.Orientation.Horizontal, self)
        self.numSlider.setTickPosition(QSlider.TicksBelow)
        self.numSlider.setMinimum(1)
        self.numSlider.setMaximum(9)
        self.numSlider.valueChanged.connect(self.valuechange)
        grid.addWidget(self.numLabel, 1, 3)
        grid.addWidget(self.numSlider, 1, 4)

        # 商品查询间隔
        self.stockLabel = QLabel(STOCK_LABEL_FORMAT.format(3))
        self.stockSlider = QSlider(Qt.Orientation.Horizontal, self)
        self.stockSlider.setTickPosition(QSlider.TicksBelow)
        self.stockSlider.setMinimum(1)
        self.stockSlider.setMaximum(9)
        self.stockSlider.valueChanged.connect(self.stockValuechange)
        grid.addWidget(self.stockLabel, 2, 3)
        grid.addWidget(self.stockSlider, 2, 4)

        # 支付密码
        passwordLabel = QLabel('支付密码')
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setEchoMode(QLineEdit.Password)
        self.passwordEdit.setPlaceholderText('使用虚拟资产时填写')
        self.passwordEdit.textChanged[str].connect(self.textChanged)
        grid.addWidget(passwordLabel, 3, 0)
        grid.addWidget(self.passwordEdit, 3, 1)

        # 开始时间
        self.buyTimeLabel = QLabel('定时开始执行时间')
        self.buyTimeEdit = QDateTimeEdit(QDateTime.currentDateTime(), self)
        self.buyTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        grid.addWidget(self.buyTimeLabel, 3, 3)
        grid.addWidget(self.buyTimeEdit, 3, 4)

        # 时间校对
        self.timeButton = QPushButton("使用JD时间（更改系统时间需管理员身份）")
        self.timeButton.clicked[bool].connect(self.initTime)
        grid.addWidget(self.timeButton, 4, 0, 1, 2)

        # 自动时间梯度
        self.autoIntervalButton = QPushButton("自动时间梯度")
        self.autoIntervalButton.clicked[bool].connect(self.autoInterval)
        grid.addWidget(self.autoIntervalButton, 4, 3)

        # 关闭proxy
        self.proxyBtn = QPushButton("Proxy：已禁用")
        os.environ['NO_PROXY'] = '*'
        self.proxyBtn.clicked[bool].connect(self.enableProxy)
        grid.addWidget(self.proxyBtn, 4, 4)

        # 二维码
        self.qrLabel = QLabel()
        grid.addWidget(self.qrLabel, 5, 0, 1, 2)
        self.qrLabel.hide()

        # 控制按钮
        self.endButton = QPushButton("结束")
        self.endButton.clicked[bool].connect(self.onClick)
        self.startButton = QPushButton("开始")
        self.startButton.clicked[bool].connect(self.onClick)
        grid.addWidget(self.endButton, 6, 0, 1, 2)
        grid.addWidget(self.startButton, 6, 3, 1, 2)

        self.endButton.setDisabled(True)

        # 信息展示（登录状态）
        self.infoLabel = QLabel()
        self.infoLabel.setText(
            "当前登录状态是: {0}".format('已登录' if self.session.isLogin else '未登录'))
        grid.addWidget(self.infoLabel, 7, 0, 1, 2)

        # 信息展示（对时）
        self.infoLabel_t = QLabel()
        self.updateInfo_t("自动时间梯度：未开启", "")
        grid.addWidget(self.infoLabel_t, 7, 3, 1, 2)

        self.setLayout(grid)

        # self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('京东小猪手')
        self.show()

    # 开启下单任务
    def startTask(self):
        if not self.session.isLogin:
            self.qrLogin()
            self.infoLabel.setText('请使用京东扫码登录')
            logger.info('请使用京东扫码登录')
            return
        self.config['buyTime'] = self.buyTimeEdit.text()
        self.config['skuId'] = self.skuEdit.text()
        self.config['areaId'] = self.areaEdit.text()
        self.saveData()
        self.buyerThread = BuyerThread(self.session, self.config)
        self.buyerThread.infoSignal.connect(self.infoSignal)
        self.buyerThread.start()

    # 扫码登录
    def qrLogin(self):
        res = self.session.getQRcode()
        img = QImage.fromData(res)
        self.qrLabel.setPixmap(QPixmap.fromImage(img))
        self.qrLabel.show()
        self.ticketThread.start()

    # 异步线程信号
    def ticketSignal(self, sec):
        self.qrLabel.hide()
        if sec == '成功':
            self.startTask()
        else:
            # 失败
            self.infoLabel.setText(sec)
            self.resumeStartBtn()

    def infoSignal(self, sec):
        self.qrLabel.hide()
        self.infoLabel.setText(sec)

    # WhXcjm
    def initTime(self, pressed, changeSystemTime=True):
        self.timeButton.setDisabled(True)
        global jd_time_on
        jd_time_on=True
        for i in range(3):
            jd_1 = JDTime.time()
            time.sleep(0.1)
        jd_1 = JDTime.time()
        loc = datetime.now()
        jd_2 = JDTime.time()
        delt = (jd_2 - jd_1) / 2
        if (changeSystemTime):
            jd = JDTime.time()
            JDTime.settime(jd + delt)
            self.initTime(pressed=False, changeSystemTime=False)
            return True
        else:
            jd_1 = JDTime.time()
            loc = datetime.now()
            jd_2 = JDTime.time()
            global averJDMinusSystem
            delta_interval_1 = loc - jd_1
            delta_interval_2 = jd_2 - loc
            print("delta_interval_1 = loc - jd_1 = {0}\n\
delta_interval_2 = jd_2 - loc = {1}".format(delta_interval_1.total_seconds(),
                                            delta_interval_2.total_seconds()))
            dt = (jd_2 - jd_1).total_seconds() / 2
            self.updateInfo_t(t2="延迟：%.3fs" % (dt))
            averJDMinusSystem = jd_1 + (jd_2 - jd_1) / 2 - loc
            print("averJDMinusSystem={0}".format(
                averJDMinusSystem.total_seconds()))
            self.timeButton.setDisabled(False)

    def autoInterval(self, pressed):
        global auto_interval_on
        if (auto_interval_on):
            # Disable autointerval
            auto_interval_on = False
            self.updateInfo_t("自动时间梯度：已关闭")
            self.buyTimeLabel.setText("定时开始执行时间")
            self.stockSlider.setEnabled(True)
        else:
            # Enable autointerval
            self.initTime(False, changeSystemTime=False)
            auto_interval_on = True
            self.updateInfo_t("自动时间梯度：已开启")
            self.buyTimeLabel.setText("自动抢购正点时间")
            self.stockSlider.setEnabled(False)

    global infotext

    def updateInfo_t(self, t1="__OCCUPIED", t2="__OCCUPIED"):
        global infotext
        if (t1 == "__OCCUPIED"):
            t1 = infotext[0]
        if (t2 == "__OCCUPIED"):
            t2 = infotext[1]
        self.infoLabel_t.setText(str(t1) + '  ' + str(t2))
        infotext[0] = t1
        infotext[1] = t2
        return

    def enableProxy(self):
        if (os.getenv('NO_PROXY') == '*'):
            os.environ['NO_PROXY'] = ''
            self.proxyBtn.setText("Proxy：已开启")
        else:
            os.environ['NO_PROXY'] = '*'
            self.proxyBtn.setText("Proxy：已禁用")

    # 按钮监听
    def onClick(self, pressed):
        source = self.sender()
        if source.text() == '开始':
            self.startTask()
            self.disableStartBtn()
        if source.text() == '结束':
            self.handleStopBrn()

    def handleStopBrn(self):
        if self.session.isLogin:
            self.buyerThread.pause()
        else:
            self.ticketThread.pause()
        self.resumeStartBtn()

    def disableStartBtn(self):
        self.endButton.setDisabled(False)
        self.startButton.setDisabled(True)

    def resumeStartBtn(self):
        self.endButton.setDisabled(True)
        self.startButton.setDisabled(False)

    # 输入框监听
    def textChanged(self, text):
        password = self.passwordEdit.text()
        self.config['password'] = password
        self.session.password = password

    # 滑块监控
    def valuechange(self):
        num = self.numSlider.value()
        self.config['count'] = num
        self.numLabel.setText(NUM_LABEL_FORMAT.format(num))

    def stockValuechange(self):
        stock = self.stockSlider.value()
        self.config['stockInterval'] = stock
        self.stockLabel.setText(STOCK_LABEL_FORMAT.format(stock))


# 登录监控线程


class TicketThread(QThread):
    """ check ticket
    """
    ticketSignal = Signal(str)

    def __init__(self, session):
        super().__init__()
        self.session = session
        self._isPause = False

    def pause(self):
        self._isPause = True

    def run(self):
        self._isPause = False
        ticket = None
        retry_times = 85
        for i in range(retry_times):
            if self._isPause:
                self.ticketSignal.emit('已取消登录')
                return
            ticket = self.session.getQRcodeTicket()
            if ticket:
                break
            time.sleep(2)
        else:
            self.ticketSignal.emit('二维码过期，请重新获取扫描')
            return

        # validate QR code ticket
        if not self.session.validateQRcodeTicket(ticket):
            self.ticketSignal.emit('二维码信息校验失败')
            return

        self.ticketSignal.emit('成功')
        self.session.isLogin = True
        self.session.saveCookies()


# 商品监控线程


class BuyerThread(QThread):

    infoSignal = Signal(str)

    def __init__(self, session, taskParam):
        super().__init__()
        self.session = session
        self.taskParam = taskParam
        self._isPause = False

    def pause(self):
        self._isPause = True
        self.timer.stop()

    # just a try
    tsParam = '时间：{0} 剩余：>5min 间隔：60s {1} 抢购开始'

    def timeSignal(self, sec):
        # print("timeSignal(sec:{0})\n emit{1}".format(
        #     datetime.now(),
        #     self.tsParam.format(sec, self.taskParam.get('buyTime'))))
        self.infoSignal.emit(
            self.tsParam.format(sec.strftime(DATA_FORMAT), self.taskParam.get('buyTime')))

    # just a try

    def run(self):
        global averJDMinusSystem

        def isPaused():
            if self._isPause:
                self.infoSignal.emit('{0} 已取消下单'.format(
                    (datetime.now() +
                     (averJDMinusSystem if jd_time_on == True else
                      timedelta(seconds=0))).strftime(DATA_FORMAT)))
                return True
            else:
                return False

        sku_id = self.taskParam.get('skuId')
        area_id = self.taskParam.get('areaId')
        count = self.taskParam.get('count')
        stock_interval = self.taskParam.get('stockInterval')
        buyTime = self.taskParam.get('buyTime')

        self.session.fetchItemDetail(sku_id)
        submitRetry = 3
        submitInterval = 5
        if (auto_interval_on):

            self.timer = Timer(buyTime, 1, 60, jd_time_on, averJDMinusSystem)
            JdBuyerUI.initTime(ui, False, changeSystemTime=False)
            self.tsParam = '时间：{0} 剩余：>1min 间隔：0.1s {1} 抢购开始'
            self.timer.infoSignal.connect(self.timeSignal)
            if (isPaused()):
                return
            self.timer.start()
            self.timer.wait()

            self.timer = Timer(buyTime, 0.002, 0.03, jd_time_on, averJDMinusSystem)
            #建议advance值使用【延迟值*0.7】 && 做好保险，为了到0.02s内而承担超出0.1s的风险不是很值得吧
            self.tsParam = '时间：{0} 剩余：<1min 间隔：0.002s {1} 抢购开始'
            if (isPaused()):
                return
            self.timer.start()
            self.timer.wait()
            stock_interval = 0.001
            if (isPaused()):
                return
        else:
            self.timer = Timer(buyTime)
            self.tsParam='定时中，当前时间 {0} ，将于 {1} 开始执行'
            if (isPaused()):
                return
            self.timer.infoSignal.connect(self.timeSignal)
            self.timer.start()
            self.timer.wait()
            if (isPaused()):
                return
        # 防封号设计
        # 实践出真寄=>已经改为较保守设计
        counter = 0
        print("开始抢购")
        while True:
            if(auto_interval_on):
                counter += 1
                if (counter > 10):
                    if (counter > 20):
                        if (counter > 74):
                            if (counter > 110):
                                if (counter > 170):
                                    if (counter > 270):
                                        if (counter > 307):
                                            #>307
                                            print("回到监测状态")
                                            stock_interval = 188
                                        else:
                                            #270-307
                                            print("十多分钟了，累了&泪了，随心刷刷，随它去吧")
                                            stock_interval = 23.9
                                    else:
                                        #170-270
                                        print("刷了五分钟了，随它去吧，全凭天意")
                                        stock_interval = 3
                                else:
                                    #110-170
                                    print("刷了四分钟左右了，（可能）进入退款高峰，提高频次")
                                    stock_interval = 0.9
                            else:
                                #74-110
                                print("刷了一分钟了，降低频次")
                                stock_interval = 5
                        else:
                            #20-74
                            print("6s过去，开始期待有人退款，按正常人手速来买")
                            stock_interval = 0.9
                    else:
                        #10~20
                        print("1s过去，基本上就没货了，改小参数")
                        stock_interval = 0.4

            if (isPaused()):
                return
            try:
                if not self.session.getItemStock(
                        skuId=sku_id, skuNum=1, areaId=area_id):
                    self.infoSignal.emit('{0} 不满足下单条件，{1}s后进行下一次查询'.format(
                        (datetime.now() +
                         (averJDMinusSystem if jd_time_on == True else
                          timedelta(seconds=0))).strftime(DATA_FORMAT),
                        stock_interval))
                else:
                    self.infoSignal.emit('{0} 满足下单条件，开始执行'.format(sku_id))
                    if not self.session.prepareCart(sku_id, count, area_id):
                        self.infoSignal.emit('{0} 加入购物车失败，{1}s后进行下一次查询'.format(
                            (datetime.now() +
                             (averJDMinusSystem if jd_time_on == True
                              else timedelta(seconds=0))
                             ).strftime(DATA_FORMAT), stock_interval))
                    else:
                        if self.session.submitOrderWitchTry(
                                submitRetry, submitInterval):
                            self.infoSignal.emit('下单成功')
                            return
            except Exception as e:
                self.infoSignal.emit(e)
                print(e)
            time.sleep(stock_interval)


ui = 0


def main():
    app = QApplication(sys.argv)
    global ui
    ui = JdBuyerUI()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
