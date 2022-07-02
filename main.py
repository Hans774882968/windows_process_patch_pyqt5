from win32gui import FindWindow
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import pyqtSignal, QThread
from different_flag_ui import Ui_MainWindow
from PyQt5 import QtCore
import sys
from trainer import *

LB, UB = -2147483648, 2147483646
wanted_window_classname = "ConsoleWindowClass"
wanted_window_title = r"不一样的flag.exe"


class MonitorThread(QThread):
    get_proc_signal = pyqtSignal(int, int, int)
    get_maze_signal = pyqtSignal(str)
    get_pos_signal = pyqtSignal(int, int)
    proc_exist_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            hWnd = FindWindow(wanted_window_classname, wanted_window_title)
            if not hWnd:
                self.get_proc_signal.emit(0, 0, 0)
                self.get_maze_signal.emit("")
                self.get_pos_signal.emit(UB + 1, UB + 1)
                self.proc_exist_signal.emit(False)
            else:
                hProcess, pid = getProcessHandle(hWnd)
                self.get_proc_signal.emit(hWnd, pid, hProcess)
                # 读迷宫字符串
                bs = readMemStr(hProcess, 0x402000, 26)
                self.get_maze_signal.emit(bs.decode("utf-8", "ignore"))
                # 读人物坐标
                esp = 0x60FEB0
                xAddr = esp + 0x30
                yAddr = esp + 0x34
                x = readMemVal(hProcess, xAddr, 4)
                y = readMemVal(hProcess, yAddr, 4)
                self.get_pos_signal.emit(x, y)
                self.proc_exist_signal.emit(True)
            time.sleep(1)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.hProcess = 0
        self.pid = 0

        self.allowObstacle.stateChanged.connect(self.allowObstacleChange)
        self.allowIllegalInput.stateChanged.connect(
            self.allowIllegalInputChange)

        self.modifyButton.clicked.connect(self.modifyPos)
        intValidator1 = QIntValidator(LB, UB)
        intValidator2 = QIntValidator(LB, UB)
        self.xLineEdit.setValidator(intValidator1)
        self.yLineEdit.setValidator(intValidator2)

        self.monitor_thread = MonitorThread()
        self.monitor_thread.get_proc_signal.connect(self.set_process_info)
        self.monitor_thread.get_maze_signal.connect(self.set_maze_label)
        self.monitor_thread.get_pos_signal.connect(self.set_pos_label)
        self.monitor_thread.proc_exist_signal.connect(
            self.set_ui_enabled_state)
        self.monitor_thread.start()

    def set_ui_enabled_state(self, fl):
        self.allowObstacle.setEnabled(fl)
        self.allowIllegalInput.setEnabled(fl)
        self.modifyButton.setEnabled(fl)
        if not fl:
            self.allowObstacle.setChecked(False)
            self.allowIllegalInput.setChecked(False)

    def set_process_info(self, hWnd, pid, hProcess):
        self.hProcess = hProcess
        self.pid = pid
        self.processInfo.setText(
            "不一样的flag.exe " +
            ("hWnd = %s，进程pid = %s" % (hex(hWnd), self.pid) if hWnd else
             "not found"))

    def set_maze_label(self, s):
        if not s:
            self.mazeLabel.setText("未检测到“不一样的flag.exe”进程")
            return
        maze_str = "\n".join([s[i * 5:i * 5 + 5] for i in range(5)])
        self.mazeLabel.setText(maze_str)

    def set_pos_label(self, x, y):
        if x == UB + 1:
            self.posLabel.setText("未检测到“不一样的flag.exe”进程")
            return
        self.posLabel.setText("当前人物坐标：（%s，%s）" % (x, y))

    def allowObstacleChange(self):
        isChecked = self.allowObstacle.isChecked()
        # 进程不存在
        if not self.pid:
            return
        print("allowObstacle", isChecked, "pid = %s" % self.pid)
        setAllowObstacle(self.hProcess, isChecked)

    def allowIllegalInputChange(self):
        isChecked = self.allowIllegalInput.isChecked()
        # 进程不存在
        if not self.pid:
            return
        print("allowIllegalInput", isChecked, "pid = %s" % self.pid)
        setAllowIllegalInput(self.hProcess, isChecked)

    def modifyPos(self):
        try:
            x = int(self.xLineEdit.text())
        except BaseException:
            x = 0
        try:
            y = int(self.yLineEdit.text())
        except BaseException:
            y = 0
        modifyPos(x, y, self.hProcess)


if __name__ == "__main__":
    # 本机分辨率较高，使用以下语句即可让按钮大小符合期望
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    x = MainWindow()
    x.show()
    sys.exit(app.exec_())
