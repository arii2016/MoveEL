# coding: UTF-8

import sys, os, time
import serial
import Tkinter


root = Tkinter.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))


Bt_Move = Tkinter.Button(root, text='実行', width=8, height=5, font=("", 32))
Bt_Move.pack(expand=True)

root.mainloop()
