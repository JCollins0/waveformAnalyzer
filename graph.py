import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import keyboard

import tkinter as tk
import tkinter.filedialog as fd
import sys

import os
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def on_graph_close(_):
    global graphing_open
    graphing_open = False

def plot_graph(row_number,num_rows,max_y_value,auto_scale=False):
    global df
    plt.clf()
    row = df.iloc[row_number]
    row.plot(kind='line',figsize=(15,7))
    figure = plt.gcf()
    figure.canvas.mpl_connect('close_event', on_graph_close)
    plt.title(label=f"Showing row {row_number+1} of {num_rows} from {file_name_entry.split('/')[-1]}\n(comma) - go back a frame\n(period) - go forward a frame\n(space) - toggle auto progress | currently: {'on' if auto_progress else 'off'}")
    if not auto_scale:
        plt.ylim(-max_y_value, max_y_value)
    plt.draw()
    plt.pause(0.01)

def on_prev(_):
    global graphing_open
    global current_row

    if not graphing_open:
        return
    # _ is Keyboard event
    current_row = max(current_row - 1,0)

def on_next(_):
    global graphing_open
    global current_row

    if not graphing_open:
        return
    # _ is Keyboard event
    current_row = current_row + 1

def on_pause(_):
    global graphing_open
    if not graphing_open:
        return
    global auto_progress
    auto_progress = not auto_progress

def window_on_exit():
    global window_open
    global window
    window_open = False
    window.destroy()
    sys.exit()

keyboard.on_press_key(",", on_prev)
keyboard.on_press_key(".", on_next)
keyboard.on_press_key(" ", on_pause)


def graphing_loop(_):
    global graphing_open
    global current_row
    global df
    global auto_progress
    global window_open

    if file_name_entry is None or file_name_entry == "":
        return
    CONSTANTS={}
    try:
        CONSTANTS={
            'FILE_NAME':file_name_entry,
            'AUTO_SCALE':auto_scale_checked_var.get() == 1,
            'MAX_Y_VALUE':int(y_value_entry.get().replace(',','') if y_value_entry.get() != "" else "40000"),
            'SLEEP_SECONDS':.5,
            'AUTO_PROGRESS' : auto_progress_checked_var.get() == 1,
            'AUTO_SLEEP_SECONDS':max(float( auto_progress_time_entry.get() if auto_progress_time_entry.get() != "" else ".1"),.1),
        }
    except Exception as e:
        with open('log.txt','w') as log:
            log.write(str(e))
        sys.exit()

    window_open = True
    graphing_open = True
    auto_progress = CONSTANTS['AUTO_PROGRESS']

    plt.close("all")

    df = pd.read_csv(CONSTANTS['FILE_NAME'],header=None)
    num_rows = len(df)
    current_row=0
    plt.ion()
    plt.show()

    already_drew_row = 0
    plot_graph(current_row,num_rows,CONSTANTS['MAX_Y_VALUE'],auto_scale=CONSTANTS['AUTO_SCALE'])

    while current_row < num_rows and window_open and graphing_open:
        if not already_drew_row == current_row:
            plot_graph(current_row,num_rows,CONSTANTS['MAX_Y_VALUE'],auto_scale=CONSTANTS['AUTO_SCALE'])

        already_drew_row = current_row

        if auto_progress:
            current_row = current_row + 1
            plt.pause(CONSTANTS['AUTO_SLEEP_SECONDS'])
            if current_row == num_rows - 1:
                auto_progress = False

        plt.pause(CONSTANTS['SLEEP_SECONDS'])
    plt.close("all")
    graphing_open = False

window = tk.Tk()
window.title("WaveFormAnalyzer")
window.iconbitmap(resource_path("images/waveform.ico"))

file_name_entry = None
def set_file_name(_):
    global file_name_entry
    file_name_entry = fd.askopenfilename()

file_button = tk.Button(text="Open File")
file_button.bind("<Button-1>", set_file_name)
file_button.pack()

tk.Label(text="Do you want to auto scale the Y-axis? ").pack()
auto_scale_checked_var = tk.IntVar()
auto_scale_checkbutton = tk.Checkbutton(window, text="Auto Scale",variable=auto_scale_checked_var)
auto_scale_checkbutton.pack()

tk.Label(text="Enter Y Scale Value (Will not be used if auto scale is checked): ").pack()
y_value_entry = tk.Entry(fg="black", bg="white", width=50, textvariable=tk.StringVar(value="40,000"))
y_value_entry.pack()


tk.Label(text="Do you want to auto progress through rows? ").pack()
auto_progress_checked_var = tk.IntVar()
auto_progress_checkbutton = tk.Checkbutton(window, text="Auto Progress",variable=auto_progress_checked_var)
auto_progress_checkbutton.pack()

tk.Label(text="Enter time in seconds to sleep during auto progress: ").pack()
auto_progress_time_entry = tk.Entry(fg="black", bg="white", width=50,textvariable=tk.StringVar(value="3"))
auto_progress_time_entry.pack()

start_button = tk.Button(text="Start Visual")
start_button.bind("<Button-1>", graphing_loop)
start_button.pack()

graphing_open = False
auto_progress = True

window.eval('tk::PlaceWindow . center')
window.protocol('WM_DELETE_WINDOW', window_on_exit)
window.mainloop()
