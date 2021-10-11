import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import keyboard

import tkinter as tk
import tkinter.filedialog as fd
import sys
import re
import math

import os
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

def remove_number_format(string,convert_type="float",return_as="number"):
    if return_as == "string":
        return string.replace(',','')
    if convert_type=="int":
        return int(string.replace(',',''))
    return float(string.replace(',',''))

def get_multipler(time_units):
    tu = time_units.lower()
    if tu == 's':
        return 1e+9
    if tu == 'ms':
        return 1e+6
    if tu == 'ns':
        return 1
    if tu == 'm':
        return 6e+10
    if tu == 'h':
        return 3.6e+12

REGEX_PATTERN='([\d|\.]+|[A-Za-z]+)'
def convert_time_to_col(time, time_per_col="16ns"):
    units_time_val,units_time_units = re.findall(REGEX_PATTERN, time_per_col)
    units_time_val = float(units_time_val)
    # goal to convert everything to nanoseconds
    multipler = get_multipler(units_time_units)
    units_time_val *= multipler

    time_val, time_units = re.findall(REGEX_PATTERN, time)
    time_val = float(time_val)
    multipler = get_multipler(time_units)
    time_val *= multipler

    return int(time_val / units_time_val)

def convert_col_to_time(column, time_per_col="16ns"):
    units_time_val,units_time_units = re.findall(REGEX_PATTERN, time_per_col)
    units_time_val = float(units_time_val)

    return f"{round(column * units_time_val, 2)}ns"

def get_time(time_from_user_input,entered_units,total_time):
    end_time = time_from_user_input
    if end_time == "":
        end_time = total_time
        return f"{end_time}ns"
    else:
        end_time = min(float(end_time), total_time)
        return f"{end_time}{entered_units}"

    return f"0ns" # should never get here


def on_graph_close(_):
    global graphing_open
    graphing_open = False

OFFSET = lambda columns : 10 ** int(math.log(columns,10)-1)  # for viewing plot easier
def plot_graph(row_number,num_rows,max_y_value,min_x_value,max_x_value,auto_scale=False):
    global df
    plt.clf()
    row = df.iloc[row_number][min_x_value : max_x_value]
    myplot = row.plot(kind='line',figsize=(15,8))
    figure = plt.gcf()
    figure.canvas.mpl_connect('close_event', on_graph_close)

    hovered_time="0ns"

    # closures require we pass this time otherwise it will always be 0ns
    def update_plot_title(hovered_time):
        plt.title(label=f"Showing row {row_number} of {num_rows-1} from {file_name_entry.split('/')[-1]}"+
                f"\nViewing time {convert_col_to_time(min_x_value)} to {convert_col_to_time(max_x_value)} - Hovered Over t={hovered_time}" +
                f"\n(comma) - go back a frame (period) - go forward a frame\n(space) - toggle auto progress | currently: {'on' if auto_progress else 'off'}")

    def on_plot_hover(event):
    # Iterating over each data member plotted
        for curve in myplot.get_lines():
            # Searching which data member corresponds to current mouse position
            if curve.contains(event)[0]:
                hovered_time=convert_col_to_time(event.xdata)
                update_plot_title(hovered_time)

    figure.canvas.mpl_connect('motion_notify_event', on_plot_hover)
    update_plot_title(hovered_time)


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

time_per_column = 16.1 ## nano seconds (ns)
time_per_column_string = f"{time_per_column}ns"

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
            'MAX_Y_VALUE': remove_number_format(y_value_entry.get() if y_value_entry.get() != "" else "0"),
            'ROW_START' : remove_number_format(row_start_entry.get() if row_start_entry.get() != "" else "0", convert_type="int"),
            'SLEEP_SECONDS':.5,
            'AUTO_PROGRESS' : auto_progress_checked_var.get() == 1,
            'AUTO_SLEEP_SECONDS':max( remove_number_format( auto_progress_time_entry.get() if auto_progress_time_entry.get() != "" else ".1"),.1),
            'START_TIME' : remove_number_format(col_start_entry.get(),return_as="string"),
            'END_TIME' : remove_number_format(col_end_entry.get(),return_as="string"),
            'TIME_UNITS': "ns" if units_var.get() == 1 else ("ms" if units_var.get() == 2 else "s"),
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
    num_cols = len(df.columns)


    total_time = time_per_column * num_cols

    CONSTANTS['START_TIME_FORMATTED'] = get_time(CONSTANTS['START_TIME'], CONSTANTS['TIME_UNITS'],total_time)
    CONSTANTS['XLIM_START'] = convert_time_to_col(CONSTANTS['START_TIME_FORMATTED'],time_per_col=time_per_column_string)
    CONSTANTS['END_TIME_FORMATTED'] = get_time(CONSTANTS['END_TIME'], CONSTANTS['TIME_UNITS'],total_time)
    CONSTANTS['XLIM_END'] = convert_time_to_col(CONSTANTS['END_TIME_FORMATTED'],time_per_col=time_per_column_string)

    current_row=min(CONSTANTS['ROW_START'],num_rows-1)
    plt.ion()
    plt.show()
    already_drew_row = current_row
    plot_graph(row_number=current_row,
               num_rows=num_rows,
               max_y_value=CONSTANTS['MAX_Y_VALUE'],
               min_x_value=CONSTANTS['XLIM_START'],
               max_x_value=CONSTANTS['XLIM_END'],
               auto_scale=CONSTANTS['AUTO_SCALE'])

    while current_row < num_rows and window_open and graphing_open:
        if not already_drew_row == current_row:
            plot_graph(row_number=current_row,
                       num_rows=num_rows,
                       max_y_value=CONSTANTS['MAX_Y_VALUE'],
                       min_x_value=CONSTANTS['XLIM_START'],
                       max_x_value=CONSTANTS['XLIM_END'],
                       auto_scale=CONSTANTS['AUTO_SCALE'])

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

frame = tk.Frame(window)

file_name_entry = None
def set_file_name(_):
    global file_name_entry
    file_name_entry = fd.askopenfilename(filetypes=[("CSV","*.csv")])

file_button = tk.Button(frame,text="Open File")
file_button.bind("<Button-1>", set_file_name)
file_button.pack()

tk.Label(frame, text="Do you want to auto scale the Y-axis? ").pack()
auto_scale_checked_var = tk.IntVar()
auto_scale_checkbutton = tk.Checkbutton(frame, text="Auto Scale",variable=auto_scale_checked_var)
auto_scale_checkbutton.pack()

tk.Label(frame,text="Enter Y Scale Value (Will not be used if auto scale is checked): ").pack()
y_value_entry = tk.Entry(frame,fg="black", bg="white", width=50, textvariable=tk.StringVar(value="40,000"))
y_value_entry.pack()

tk.Label(frame,text="Enter Starting Row").pack()
row_start_entry = tk.Entry(frame,fg="black", bg="white", width=50, textvariable=tk.StringVar(value="0"))
row_start_entry.pack()

tk.Label(frame,text="Do you want to auto progress through rows? ").pack()
auto_progress_checked_var = tk.IntVar()
auto_progress_checkbutton = tk.Checkbutton(frame, text="Auto Progress",variable=auto_progress_checked_var)
auto_progress_checkbutton.pack()

tk.Label(frame,text="Enter time in seconds to sleep during auto progress: ").pack()
auto_progress_time_entry = tk.Entry(frame,fg="black", bg="white", width=50,textvariable=tk.StringVar(value="2"))
auto_progress_time_entry.pack()

frame2 = tk.Frame(frame)
tk.Label(frame, text=f"Enter start and end time (time per column is: {time_per_column_string}) ").pack()
col_start_entry = tk.Entry(frame2, fg="black", bg="white", width=20,textvariable=tk.StringVar(value="0"))
col_start_entry.grid(row=0,column=0)
# col_start_entry.pack()
tk.Label(frame2, text="to",width=10).grid(row=0,column=1)
col_end_entry = tk.Entry(frame2, fg="black", bg="white", width=20)
col_end_entry.grid(row=0,column=2)

units_var = tk.IntVar(value=1)
tk.Radiobutton(frame2,text="ns",width=2,variable=units_var,value=1).grid(row=1,column=0)
tk.Radiobutton(frame2,text="ms",width=2,variable=units_var,value=2).grid(row=1,column=1)
tk.Radiobutton(frame2,text="s",width=2,variable=units_var,value=3).grid(row=1,column=2)


# col_end_entry.pack()
frame2.pack()

start_button = tk.Button(frame, text="Start Visual")
start_button.bind("<Button-1>", graphing_loop)
start_button.pack()

frame.pack()


graphing_open = False
auto_progress = True

window.eval('tk::PlaceWindow . center')
window.protocol('WM_DELETE_WINDOW', window_on_exit)
window.mainloop()
