from tkinter import *
from tkinter import ttk
from tkinter import filedialog

def select_directory():
    directory = filedialog.askdirectory()
    print(directory)

root = Tk()
root.title('PicPrune')
root.minsize(width=800, height=500)
frm = ttk.Frame(root, padding=10)

frm.grid()
ttk.Button(frm, text="Select Directory", command=select_directory).grid(column=0, row=0)

root.mainloop()