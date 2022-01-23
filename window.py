import tkinter as tk
from tkinter import ttk

import datetime
from dateutil.relativedelta import relativedelta
from threading import Thread
import os
import platform
import subprocess

from mail_connection import EmailConnector
from invoice_detector import InvoiceDetection

now = datetime.date.today()

class SystemWindow(tk.Tk):
    OPTIONS = [(now - relativedelta(months=i)).strftime("%m-%Y") for i in range(12) ]
    
    def __init__(self, window_title: str):
        """Initialize window and render all the elements"""
        super().__init__(className=window_title)
        
        # Position the window in the screen
        self.geometry("350x150+400+250")
        
        # Declare select_date input
        self.selected_date = tk.StringVar(self)
        self.selected_date.set(self.OPTIONS[0]) 
        
        # Declare other inputs
        tk.Label(self, text="Email").grid(row=0)
        tk.Label(self, text="Password").grid(row=1)
        tk.Label(self, text="Month").grid(row=2)
        
        self.email_input = tk.Entry(self)
        self.password_input = tk.Entry(self, show="*")
        
        self.password_input.grid(row=1, column=1)
        self.email_input.grid(row=0, column=1)

        self.w = tk.OptionMenu(self, self.selected_date, *self.OPTIONS)
        self.w.grid(row=2, column=1)

        # progressbar
        self.pb = ttk.Progressbar(
            self,
            orient='horizontal',
            mode='indeterminate',
            length=280
        )
        
        # place the progressbar
        self.pb.place(x=30, y=130)

        # Declare buttons
        tk.Button(self, text='Quit', command=self.quit).place(x=50, y=100)

        self.download_button = tk.Button(self, text='Download', command=self.submit_data_and_retrieve_messages)
        self.download_button.place(x=200, y=100)

    def submit_data_and_retrieve_messages(self):
        """Submit inserted data by the user and try to retrieve attachments from email messages"""
        email = self.email_input.get()
        password = self.password_input.get()
        selected_date = self.selected_date.get()
        
        # Clear inputs and start the progress bar animation
        self.email_input.delete(0, tk.END)
        self.password_input.delete(0, tk.END)
        self.pb.start()
        
        # Declare that we'd like to retrieve only PDF files
        desired_file_extension = ".pdf"
        
        # Run the email connector method retrieving messages in the separate thread 
        # To keep the window working smoothly
        email_connector = EmailConnector(email, password)
        t1 = Thread(target=email_connector.retrieve_attachments_from_month, args=(selected_date, desired_file_extension))
        t1.start()
        
        # Disable inputs and update window on thread changes
        self.disable_inputs()
        self.monitor(t1)
        
    def disable_inputs(self):
        """Disable all the inputs when retrieving data"""
        self.download_button['state'] = tk.DISABLED
        self.email_input['state'] = tk.DISABLED
        self.password_input['state'] = tk.DISABLED
    
    def enable_inputs(self):
        self.download_button['state'] = tk.NORMAL
        self.email_input['state'] = tk.NORMAL
        self.password_input['state'] = tk.NORMAL
        
    def popup_window(self, message: str):
        """Create a popup window displaying given message"""
        top = tk.Toplevel(self)
        top.geometry("400x100+400+250")
        top.title("Info")
        tk.Label(top, text=message).place(x=10,y=5)
        
    def open_file(self, path):
        """Open the directory with system files browser"""
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    
    def monitor(self, thread):
        """Check if the Thread is still running and adjust window components accordingly"""
        if thread.is_alive():
            # check the thread every 100ms
            self.after(100, lambda: self.monitor(thread))
        else:
            # Detect invoices in among collected files
            invoice_detector = InvoiceDetection()
            invoice_detector.multiprocessing_detect_data_from_pdf("faktura")
            
            # self.popup_window("My work is done here! Check the attachments/ catalogue :)")
            self.pb.stop()
            # self.enable_inputs()
            self.open_file("./attachments/")
            self.destroy()