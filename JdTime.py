import requests
import datetime
import time
import pytz
import win32api
import ctypes
import sys
from utils import get_random_useragent

class JDTime(object):

    def isAdmin():
        """判断当前用户是否是管理员"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def settime(t):
        '''Requires administrator privileges'''
        pytz.timezone('UTC')
        t.astimezone()
        if (JDTime.isAdmin()):
            print((t.year, t.month, (t.weekday() + 1) % 7, t.day, t.hour,
                   t.minute, t.second, int(t.microsecond / 1000)))
            win32api.SetSystemTime(t.year, t.month, (t.weekday() + 1) % 7,
                                   t.day, ((t.hour - 8) % 24 + 24) % 24,
                                   t.minute, t.second,
                                   int(t.microsecond / 1000))
            # 注：0-6在datetime中是周一到周日，在win32中是周日-周一-周六
        else:
            # # 重新运行这个程序使用管理员权限 注：似乎完全无效&求教其解决方案
            # print("使用管理员权限运行该程序")
            # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable,
            #                                     __file__, None, 1)
            print("客户端无管理员权限，未更改系统时间")
    def time():
        '''JD time in local timezone'''
        try:
            re = requests.get(
                url=
                'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5',
                headers={
                    'User-Agent':
                    get_random_useragent()
                })
            res = eval(re.text)
            timeNum = int(res['currentTime2'])
            timeStamp = float(timeNum) / 1000
            ret_datetime = datetime.datetime.fromtimestamp(
                timeStamp)  # .strftime("%Y-%m-%d %H:%M:%S.%f")
            print("success&re.text:{0}".format(re.text))
            print("res:{0}".format(res))
            return ret_datetime
        except Exception as e:
            print("error:{0}".format(e))
            print("re.text:{0}".format(re.text))
            print("re.status_code:{0}".format(re.status_code))
            print("res:{0}".format(res))


if __name__ == '__main__':
    # JDTime.settime(t=datetime.datetime.now() + datetime.timedelta(minutes=5))
    print(JDTime.time())
    print(win32api.GetLocalTime())