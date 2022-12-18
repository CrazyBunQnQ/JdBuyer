import requests
import datetime
import time
import pytz
import win32api
import ctypes
import sys


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
        '''JD time in local zone'''
        re = requests.get(
            url=
            'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5',
            headers={
                'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
            })
        res = eval(re.text)
        timeNum = int(res['currentTime2'])
        timeStamp = float(timeNum) / 1000
        ret_datetime = datetime.datetime.fromtimestamp(
            timeStamp)  # .strftime("%Y-%m-%d %H:%M:%S.%f")
        return ret_datetime


if __name__ == '__main__':
    # JDTime.settime(t=datetime.datetime.now() + datetime.timedelta(minutes=5))
    print(win32api.GetLocalTime())