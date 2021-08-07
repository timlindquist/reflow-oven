import tkinter as tk
from tkinter import filedialog as fd
import numpy as np
import time
import os
import serial
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import pyplot
from matplotlib.font_manager import FontProperties

STOPPED = False
RUNNING = True

TIME_UPDATE_PERIOD = 25
DEVICE_UPDATE_PERIOD = 1000
INFO_UPDATE_PERIOD = 500

REAL_DATA_PERIOD = 1 #space data 1000ms appart

class Reflow():
    def __init__(self):
        self.state = STOPPED
        self.start_time = 0
        self.elapse_time = 0
        self.target_profile = np.array([[], []], np.uint32)
        self.real_profile = np.array([[], []], np.uint32)
        self.target_temp = 0 #target value
        self.real_temp = 0 #current
        
        
        self.window = tk.Tk()
        self.window.title('Reflow Oven')
        self.window.geometry("825x500")
        
        self.power_var = tk.IntVar()
        self.power_checkbtn = tk.Checkbutton(self.window, text = "Oven Power: OFF", font=("Times New Roman", 14), variable=self.power_var, command = self.oven_power)
        self.start_btn = tk.Button(self.window, text = 'Start', bd = '5', command = self.set_start)
        self.stop_btn = tk.Button(self.window, text = 'Stop', bd = '5', command = self.set_stop)
        
        self.file_label = tk.Label(self.window, text = 'No file chosen', font=("Times New Roman", 8), anchor='w', width = 20, height = 4, fg = 'black')
        self.file_label_1 = tk.Label(self.window, text = 'File Select:', font=("Times New Roman", 14), anchor='w', width = 20, height = 4, fg = 'black')
        self.file_btn = tk.Button(self.window, text= 'Choose File', command = self.get_file)
        
        self.info_label = tk.Label(self.window, text = '', font=("Times New Roman", 30), anchor='w', width = 30, height = 4, fg = 'black')
        device_choices = [];
        self.device = tk.StringVar(self.window)
        self.device_option = tk.OptionMenu(self.window, self.device, None, *device_choices, command = self.set_device)
        self.device_option.config(width=20)
        self.device_label = tk.Label(self.window, text = 'Device Select:', font=("Times New Roman", 14), anchor='w', width = 10, height = 4, fg = 'black')
        
        # graph
        fig = Figure(figsize = (5, 5), dpi = 100)
        self.plt = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, master = self.window)  
        self.set_plot()
        
        #placement
        p = [[500, 70], [500, 110], [500, 280], [500, 320]]
        
        self.canvas.get_tk_widget().place(x = 0, y = 0)
        
        self.file_label_1.place(x = p[0][0], y = p[0][1] - 20)
        self.file_btn.place(x = p[0][0] + 100, y = p[0][1])
        self.file_label.place(x = p[0][0] + 200, y = p[0][1])
        
        self.device_label.place(x = p[1][0], y = p[1][1] - 20)
        self.device_option.place(x = p[1][0] + 100, y = p[1][1])
        
        self.start_btn.place(x = p[2][0], y = p[2][1])
        self.stop_btn.place(x = p[2][0] + 75, y = p[2][1])
        self.power_checkbtn.place(x = p[2][0] + 150, y = p[2][1] + 5)
        
        self.info_label.place(x = p[3][0], y = p[3][1])
        
        
        self.set_device()
        self.set_info();
        
        
        self.window.mainloop()
        
    def oven_power(self):
        if self.power_var.get():
            self.power_checkbtn['text'] = "Oven Power: ON"
        else:
            self.power_checkbtn['text'] = "Oven Power: OFF"
        
    def get_device(self):
        print("get_device")
        
        
    def set_device(self):
        self.device_option['menu'].delete(0,'end')
    
        options=os.popen('ls /dev | grep usb').readlines()
    
        if (self.device.get() not in options) and (self.device.get() != ''):
            self.device.set('')
 
        for option in options:
            self.device_option['menu'].add_command(label=option, command=lambda value=option: self.device.set(value))
        
        self.device_option.after(DEVICE_UPDATE_PERIOD, self.set_device)
        
        
    def get_file(self):
        filename = fd.askopenfilename(initialdir = "~/", title = "Select a File")
    
        #parse the file
        with open(filename) as fp:
            csv_reader = csv.reader(fp, delimiter=',')
            line_count = 0
            times = []
            temps = []
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    times.append(float(row[0]))
                    temps.append(float(row[1]))
                    line_count += 1
        # Linearly interpolate points
        x = np.linspace(times[0], times[-1], (times[-1] - times[0])*REAL_DATA_PERIOD)
        y = np.interp(x, times, temps)
        self.target_profile = np.array([x, y])
        # Change label contents
        self.file_label.configure(text="Opened: " + filename.split('/')[-1])
        self.set_plot()
        
        
    def set_plot(self):
        self.plt.clear()
        font = FontProperties()
        font.set_family('serif')
        font.set_name('Times New Roman')
        self.plt.set_xlabel('Time (s)', fontproperties=font)
        self.plt.set_ylabel('Temp (C)', fontproperties=font)
        self.plt.set_title('Target vs Actual Profile', fontproperties=font)
        
        if self.target_profile.size != 0:
            self.plt.plot(self.target_profile[0,:], self.target_profile[1,:], label='Target Profile')
            self.plt.plot(self.real_profile[0,:], self.real_profile[1,:], label='Real Profile')
    
    
            if (self.elapse_time > max(self.target_profile[0,:])) and (self.state != STOPPED):
                self.set_pause(max(self.target_profile[0,:]));
                #self.set_stop()
    
            self.plt.vlines(x=self.elapse_time, ymin=0, ymax=400, colors='green', ls='-', lw=4, label='vline_single')
            self.plt.axis([0, max(self.target_profile[0,:]), 0, 400])
        
            self.canvas.draw()
    
    
    def set_start(self):
        self.start_time = time.time()
        self.start_btn['state'] = tk.DISABLED
        self.state = RUNNING
        self.run()
        
    def run(self):
        if self.state == RUNNING:
            self.elapse_time = time.time() - self.start_time;
            self.set_plot()
            self.start_btn.after(TIME_UPDATE_PERIOD, self.run)
                
    def set_stop(self):
        self.start_time = 0
        self.elapse_time = 0
        self.state = STOPPED
        self.start_btn['state'] = tk.NORMAL
        time.sleep(TIME_UPDATE_PERIOD/1000)
        self.set_plot()
        
    def set_pause(self, t_pause):
        self.state = STOPPED
        self.start_btn['state'] = tk.NORMAL
        time.sleep(TIME_UPDATE_PERIOD/1000)
        self.elapse_time = t_pause
        self.set_plot()
        
    def set_info(self):
        if (self.target_profile.size != 0) and self.power_var.get():
            x_idx = self.find_nearest(self.target_profile[0,:], self.elapse_time)
            self.target_temp = self.target_profile[1, x_idx]
        else:
            self.target_temp = 0;
        
        self.info_label.configure(text='Elapse Time: ' + 
                                str(round(self.elapse_time, 2)) + 
                                's\n Actual Temp: ' +  
                                str(round(self.real_temp, 2)) +
                                'C\nTarget Temp: ' + 
                                str(round(self.target_temp, 2)) + 'C')
        self.info_label.after(INFO_UPDATE_PERIOD, self.set_info)
        #str(round(self.real_profile[1,-1],2)) +
        
    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx
        
    def get_temp(self):
        print("get_temp")
        
        
    def set_temp(self):
        print("set_temp")
        
        
        
        
        
x = Reflow()
