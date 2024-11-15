from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import hashlib
import os

DUPLICATES_DIRECTORY_NAME = 'duplicates'
image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
directory = None
duplicatesDirectory = None

def select_directory():
    global directory
    global duplicatesDirectory
    directory = filedialog.askdirectory()
    if directory:
        selected_dir_label.config(text=directory)
        duplicatesDirectory = os.path.join(directory, DUPLICATES_DIRECTORY_NAME)

def hash_file(filename):
    with open(filename , "rb") as file:
        bytes = file.read()
        filehash = hashlib.sha256(bytes).hexdigest()
        return filehash

def get_images_in_directory(directory):
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
    images = [file for file in os.listdir(directory) if file.lower().endswith(image_extensions)]
    
    return images

def remove_duplicate_images():
    if not directory:
        return
    
    image_hashes = {}

    images = get_images_in_directory(directory)

    if not os.path.exists(duplicatesDirectory):
        os.makedirs(duplicatesDirectory)

    for img in images:
        path = os.path.join(directory, img)
        hash = hash_file(path)
        if hash in image_hashes:
            newPath = os.path.join(duplicatesDirectory, img)
            os.rename(path, newPath)
        else:
            image_hashes[hash] = path
    
    if len(os.listdir(duplicatesDirectory)) == 0:
        os.rmdir(duplicatesDirectory)


root = Tk()
root.title('PicPrune')
root.minsize(width=800, height=500)
frm = ttk.Frame(root, padding=10)

frm.grid()
ttk.Label(frm, text="Select image directory: ").grid(column=0, row=0)
ttk.Button(frm, text="->", command=select_directory).grid(column=1, row=0)
selected_dir_label = ttk.Label(frm, text="")
selected_dir_label.grid(column=0, row=1, columnspan=2, sticky="nsew")

ttk.Button(frm, text='Proceed', command=remove_duplicate_images).grid(column=0, row=2, columnspan=2, sticky='nsew')

root.mainloop()