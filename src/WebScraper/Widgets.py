import tkinter as tk
import logging
from tkinter import scrolledtext

# Custom handler
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record) + "\n"
        # Causes GUI to update in real time.
        self.text_widget.after(0, self.append, msg)


    def append(self, msg):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, msg)
        self.text_widget.configure(state="disabled")
        self.text_widget.yview(tk.END) # auto scroll