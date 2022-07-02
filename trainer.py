from win32api import OpenProcess
from win32con import PROCESS_ALL_ACCESS
from win32process import GetWindowThreadProcessId
import ctypes

kernel32 = ctypes.windll.LoadLibrary("kernel32.dll")


def getProcessHandle(hWnd):
    # 获取窗口pid
    hpid, pid = GetWindowThreadProcessId(hWnd)
    # 获取进程句柄
    hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    return hProcess, pid


def readMemVal(hProcess, address, buffLen):
    ReadProcessMemory = kernel32.ReadProcessMemory
    addr = ctypes.c_ulong()
    ReadProcessMemory(
        int(hProcess),
        address,
        ctypes.byref(addr),
        buffLen,
        None)
    return addr.value


def readMemStr(hProcess, address, buffLen):
    ReadProcessMemory = kernel32.ReadProcessMemory
    p = ctypes.create_string_buffer(buffLen)
    ReadProcessMemory(
        int(hProcess),
        address,
        p,
        buffLen,
        None)
    return p.value


def writeMemInt(hProcess, address, data):
    writeProcessInt = kernel32.WriteProcessMemory
    writeProcessInt(
        int(hProcess),
        address,
        ctypes.byref(
            ctypes.c_ulong(data)),
        4,
        None)
    return data


# data: bytes
def writeMem(hProcess, address, data, buffLen):
    writeProcess = kernel32.WriteProcessMemory
    writeProcess(
        int(hProcess),
        address,
        ctypes.c_char_p(data),
        buffLen,
        None)
    return data


# jmp = 0xeb, jnz = 0x75, jz = 0x74
def setAllowObstacle(hProcess, isChecked):
    # 判s[v1][v2] == '1'的跳转
    address = 0x40146f
    if isChecked:
        # jmp short loc_40147D
        writeMem(hProcess, address, b"\xeb\x0c", 2)
    else:
        # jnz short loc_40147D
        writeMem(hProcess, address, b"\x75\x0c", 2)
    val = readMemVal(hProcess, address, 3)
    print(hex(val))  # 小端 75 0c c7


def setAllowIllegalInput(hProcess, isChecked):
    # 判定输入是否合法：4013CF和4013DB
    ad1, ad2 = 0x4013CF, 0x4013DB
    if isChecked:
        # jmp short loc_4013DF
        writeMem(hProcess, ad1, b"\xeb\x0e", 2)
        # jmp short loc_401400
        writeMem(hProcess, ad2, b"\xeb\x23", 2)
    else:
        # jz short loc_4013DF
        writeMem(hProcess, ad1, b"\x74\x0e", 2)
        # jz short loc_401400
        writeMem(hProcess, ad2, b"\x74\x23", 2)
    val = readMemVal(hProcess, ad1, 3)
    print(hex(val))  # 小端 74 0e eb
    val = readMemVal(hProcess, ad2, 3)
    print(hex(val))  # 小端 74 23 eb


def modifyPos(x, y, hProcess):
    esp = 0x60FEB0
    xAddr = esp + 0x30
    yAddr = esp + 0x34
    writeMemInt(hProcess, xAddr, x)
    writeMemInt(hProcess, yAddr, y)
