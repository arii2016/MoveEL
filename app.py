# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports
import Tkinter
import threading

stop_flg = False

def move_thread(gcode_path):
    Bt_Move1.config(state="disable")
    Bt_Move2.config(state="disable")
    Bt_Move3.config(state="disable")
    Bt_Stop.config(state="normal")
    global stop_flg
    stop_flg = False

    move_exec(gcode_path)

    lock.release()
    Bt_Move1.config(state="normal")
    Bt_Move2.config(state="normal")
    Bt_Move3.config(state="normal")
    Bt_Stop.config(state="disable")


def move_exec(gcode_path):
    # ポート番号を取得する
    SERIAL_PORT = ""

    if sys.platform == "linux" or sys.platform == "linux2":
        matched_ports = list_ports.grep("ttyUSB")
    elif sys.platform == "darwin":
        matched_ports = list_ports.grep("cu.usbserial-")

    for match_tuple in matched_ports:
        SERIAL_PORT = match_tuple[0]
        break

    if SERIAL_PORT == "":
        return

    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=0, writeTimeout=0.1)
    except:
        return

    # Gコードモードに変更
    device.write(chr(0x11))
    device.write("?\n")

    # Gコード読み込み
    f = open(gcode_path, mode='r')
    tx_buffer = f.read() + '\nM01\n'
    f.close()

    # 入力をクリアしておく
    time.sleep(0.5)
    device.flushInput()

    # Gコード送信処理
    TX_CHUNK_SIZE = 256
    RX_CHUNK_SIZE = 256
    ready_char = '\x12'
    request_ready_char = '\x14'
    nRequested = 0
    last_request_ready = 0
    last_status_check = 0
    while True:
        if stop_flg == True:
            device.write("!")
            break
        # 受信
        chars = device.read(RX_CHUNK_SIZE)
        if len(chars) > 0:
            if 'Z' in chars:
                break
            if ready_char in chars:
                nRequested = TX_CHUNK_SIZE
                chars = chars.replace(ready_char, "")
        
        # 送信
        if len(tx_buffer) > 0:
            if nRequested > 0:
                actuallySent = device.write(tx_buffer[:nRequested])
                tx_buffer = tx_buffer[actuallySent:]
                nRequested -= actuallySent
                if nRequested <= 0:
                    last_request_ready = 0  # make sure to request ready
            elif tx_buffer[0] in ['!', '~']:  # send control chars no matter what
                actuallySent = device.write(tx_buffer[:1])
                tx_buffer = tx_buffer[actuallySent:]
            else:
                if (time.time()-last_request_ready) > 1.0:
                    actuallySent = device.write(request_ready_char)
                    if actuallySent == 1:
                        last_request_ready = time.time()
        else:
            if nRequested > 0:
                if (time.time()-last_status_check) > 1.0:
                    actuallySent = device.write("?\n")
                    if actuallySent != 0:
                        last_status_check = time.time()
                        nRequested -= actuallySent
            else:
                if (time.time()-last_request_ready) > 2.0:
                    actuallySent = device.write(request_ready_char)
                    if actuallySent == 1:
                        last_request_ready = time.time()
                    
    # コマンドモードに変更
    device.write(chr(0x13))

    device.close()

def move1_click():
    if lock.acquire(False):
        th = threading.Thread(target=move_thread, args=(HOME + "MoveEL/mass_axis_test.txt",))
        th.start()

def move2_click():
    if lock.acquire(False):
        th = threading.Thread(target=move_thread, args=(HOME + "MoveEL/hatching_test.txt",))
        th.start()

def move3_click():
    if lock.acquire(False):
        th = threading.Thread(target=move_thread, args=(HOME + "MoveEL/pro_axis_test.txt",))
        th.start()

def stop_click():
    global stop_flg
    stop_flg = True


if sys.platform == "linux" or sys.platform == "linux2":
    HOME = "/home/pi/Src/"
elif sys.platform == "darwin":
    HOME = "/Users/yoshiya/Src/workspace/"

lock = threading.Lock()

root = Tkinter.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

frame1 = Tkinter.Frame(root)
frame1.pack(side='top', expand=True, fill="x")
Bt_Move1 = Tkinter.Button(frame1, text='実行1', width=8, height=2, font=("", 20), command=move1_click, state="normal")
Bt_Move1.pack(side='left', expand=True)
Bt_Move2 = Tkinter.Button(frame1, text='実行2', width=8, height=2, font=("", 20), command=move2_click, state="normal")
Bt_Move2.pack(side='left', expand=True)

frame2 = Tkinter.Frame(root)
frame2.pack(side='top', expand=True, fill="x")
Bt_Move3 = Tkinter.Button(frame2, text='実行3', width=8, height=2, font=("", 20), command=move3_click, state="normal")
Bt_Move3.pack(side='left', expand=True)
Bt_Stop = Tkinter.Button(frame2, text='停止', width=8, height=2, font=("", 20), command=stop_click, state="disable")
Bt_Stop.pack(side='left', expand=True)

root.mainloop()
