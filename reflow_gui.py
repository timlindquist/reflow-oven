import tkinter as tk
import numpy as np
import random
import os
import serial
import csv
import time
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import pyplot
#TODO if state = False then return temp to 0C

PLOT_UPDATE_PERIOD = 10 
INFO_UPDATE_PERIOD = 500
GET_TEMP_PERIOD = 1000
SET_TEMP_PERIOD = 5000

RUN_STATE = False

def dev_connect(*args):
    print("connecting to /dev/" + str(dev.get()))
    
def dev_update():
    global prev_dev
    dev_select['menu'].delete(0,'end')
    
    options=os.popen('ls /dev | grep usb').readlines()
    
    if (dev.get() not in options) and (dev.get() != ''):
        dev.set('')
 
    for option in options:
        dev_select['menu'].add_command(label=option, command=lambda value=option: dev.set(value))
        
    dev_select.after(1000, dev_update)



def browseFiles():
    global targetProfile
    filename = filedialog.askopenfilename(initialdir = "~/", title = "Select a File")
    
    #parse the file
    with open(filename) as fp:
        csv_reader = csv.reader(fp, delimiter=',')
        line_count = 0
        times = []
        temps = []
        for row in csv_reader:
            if line_count == 0:
                #print(f'Column names are {", ".join(row)}')
                line_count += 1
                '''if "<time (s)>, <temp (C)>" not in join(row):
                    targetProfile = np.array([[], []], np.uint32)
                    return'''
            else:
                #np.array(row[0], row[1]], np.uint32)
                times.append(row[0])
                temps.append(row[1])
                #print(f'\ttime: {row[0]}, temp: {row[1]} ')
                line_count += 1
    #TODO linearly interpolate
    targetProfile = np.array([np.array(times), np.array(temps)], np.uint32)
    #realProfile = [targetProfile[0,3], targetProfile[1,3]+random.randint(-2,2)]
    # Change label contents
    label_file_explorer.configure(text="File Opened: "+filename)
    #plotProfile()
    refreshPlot()
    
    
   
    
def initPlot():
    global plt, canvas, elapse_time
    # the figure that will contain the plot
    fig = Figure(figsize = (5, 5), dpi = 100)
    # adding the subplot
    plt = fig.add_subplot(111)
    # plotting the graph
    plt.plot(targetProfile[0,:], targetProfile[1,:])
    plt.plot(realProfile[0,:], realProfile[1,:])
    plt.set_xlabel('Time (s)')
    plt.set_ylabel('Temp (C)')
    plt.set_title('Elapse Time: ' + str(round(elapse_time,2)) + 's')
    
    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master = window)  
    canvas.draw()
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()
    # creating the Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(canvas,
                                   window)
    toolbar.update()
  
    # placing the toolbar on the Tkinter window
    canvas.get_tk_widget().pack()

def refreshPlot():
    global RUN_STATE, plt, canvas, elapse_time
        
    plt.clear()
    plt.plot(targetProfile[0,:], targetProfile[1,:], label='Target Profile')
    plt.plot(realProfile[0,:], realProfile[1,:], label='Real Profile')
    
    if elapse_time > max(targetProfile[0,:]):
        stop_button()
    
    plt.vlines(x=elapse_time, ymin=0, ymax=400, colors='green', ls=':', lw=2, label='vline_single')
    #plt.axis([0, max(targetProfile[0,:]), 0, max(targetProfile[1,:])])
    plt.axis([0, max(targetProfile[0,:]), 0, 400])
    plt.set_xlabel('Time (s)')
    plt.set_ylabel('Temp (C)')
    plt.set_title('Elapse Time: ' + str(round(elapse_time,2)) + 's')
    
    canvas.draw()
    


def start_button(*args):
    global RUN_STATE, start_time, elapse_time  
    start_time = time.time()
    start_btn['state'] = tk.DISABLED
    RUN_STATE = True
    running_state()
    
def stop_button(*args):
    global RUN_STATE, start_time, elapse_time, real_times, real_temps
    start_time = 0
    elapse_time = 0
    RUN_STATE = False
    start_btn['state'] = tk.NORMAL
    refreshPlot()
    
    
    
def running_state(): #plot/time update
    global RUN_STATE, start_time, elapse_time  
    elapse_time = time.time()-start_time
    refreshPlot()
    if RUN_STATE:
        start_btn.after(PLOT_UPDATE_PERIOD, running_state)
        
        
def get_temp():
    global RUN_STATE, elapse_time, realProfile, real_times, real_temps
    current_temp = random.randint(0,10)
    
    if not RUN_STATE:
        real_times =[]
        real_temps = []
        
    real_times.append(elapse_time);
    real_temps.append(current_temp);
        
         
    realProfile = np.array([np.array(real_times), np.array(real_temps)], np.uint32)
           
    start_btn.after(GET_TEMP_PERIOD, get_temp)
        
def set_temp():
    global RUN_STATE, elapse_time, target_temp
    #linearly interpolate to find current temp.
    
    if RUN_STATE:
        target_temp = random.randint(100,200)
    else:
        target_temp = 0
        
            
    start_btn.after(SET_TEMP_PERIOD, set_temp)
        
def get_target_temp():
    global elapse_time, targetProfile
    time_size, temp_size = realProfile.shape
    if temp_size:
        if elapse_time == 0:
            return 0
        else:
            #y=mx+b
            print("find slope")
            
    
    
    
        
def update_info():
    global realProfile, target_temp
    time_size, temp_size = realProfile.shape
    if temp_size:
        info.configure(text='Elapse Time: ' + str(round(elapse_time,2)) + 's\nCurrent Temp: ' + str(round(realProfile[1,-1],2)) + 'C\nTarget Temp: ' + str(round(target_temp,2)) + 'C')
    info.after(INFO_UPDATE_PERIOD, update_info)
    
    

###------------------------------------------------------------------------------
# Global variables
targetProfile = np.array([[], []], np.uint32)
realProfile = np.array([[], []], np.uint32)

real_times = []
real_temps = []

target_temp = 0;
temp = 0
elapse_time = 0
start_time = 0

###------------------------------------------------------------------------------
# main Tkinter window
window = tk.Tk()
window.title('Reflow Oven')
window.geometry("600x600")



###------------------------------------------------------------------------------
# Create a Start button
start_btn = tk.Button(window, text = 'Start', bd = '5', command = start_button)
stop_btn = tk.Button(window, text = 'Stop', bd = '5', command = stop_button)
'''state = tk.StringVar(value="off")
state = tk.StringVar(value="off")
start_btn = tk.Radiobutton(window, text="Start", variable=state, indicatoron=False, value="off", width=8, command = start_button)
stop_btn = tk.Radiobutton(window, text="Stop", variable=state, indicatoron=False, state=tk.DISABLED, value="off", width=8, command =  stop_button)
'''

start_btn.pack()
stop_btn.pack()



###------------------------------------------------------------------------------
# Create a File Explorer
label_file_explorer = tk.Label(window,
                            text = "File Explorer",
                            width = 100, height = 4,
                            fg = "blue")
                            
button_explore = tk.Button(window,
                        text = "Browse Files",
                        command = browseFiles)
                        
label_file_explorer.pack()                                 
button_explore.pack()                       

###------------------------------------------------------------------------------
# Create info label
info = tk.Label(window,
            text = 'Info',
            width = 100, height = 4,
            fg = "blue")
info.pack()
update_info()

###------------------------------------------------------------------------------
# Create a USB device 
dev_options = ['1','2']
dev = tk.StringVar(window)

dev_select = tk.OptionMenu(window, dev, None, *dev_options, command = dev_connect)
dev_select.config(width=20)

dev_select.pack()
dev.trace("w", dev_connect)
dev_update()
get_temp()
set_temp()


###------------------------------------------------------------------------------
# run the gui
initPlot()
window.mainloop()