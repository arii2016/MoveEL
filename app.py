# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports
import Tkinter
import threading

def move_exec():
    Bt_Move.config(state="disable")

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
        sys.stderr.write('USBが接続されていません！\n')
        Bt_Move.config(state="normal")
        return

    try:
        device = serial.Serial(SERIAL_PORT, 921600, timeout=0, writeTimeout=0.1)
    except:
        Bt_Move.config(state="normal")
        sys.stderr.write('USBが接続されていません！\n')
        return

    # Gコード読み込み
    f = open(HOME + "MoveEL/四角.txt", mode='r')
    tx_buffer = f.read() + '\nM01\n'
    f.close()

    # Gコードモードに変更
    device.write(chr(0x11))

    # Gコード送信処理
    TX_CHUNK_SIZE = 256
    RX_CHUNK_SIZE = 256
    ready_char = '\x12'
    request_ready_char = '\x14'
    nRequested = 0
    last_request_ready = 0
    last_status_check = 0
    while True:
        # 受信
        chars = device.read(RX_CHUNK_SIZE)
        if len(chars) > 0:
            print (chars)
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

    lock.release()
    Bt_Move.config(state="normal")

def move_click():
    if lock.acquire(False):
        th = threading.Thread(target=move_exec)
        th.start()

if sys.platform == "linux" or sys.platform == "linux2":
    HOME = "/home/pi/Src/"
elif sys.platform == "darwin":
    HOME = "/Users/yoshiya/Src/workspace/"

lock = threading.Lock()

root = Tkinter.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

Bt_Move = Tkinter.Button(root, text='実行', width=8, height=5, font=("", 32), command=move_click)
Bt_Move.pack(expand=True)

root.mainloop()
