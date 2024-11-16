from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import hashlib
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import os

DUPLICATES_DIRECTORY_NAME = 'duplicates'
SIMILARITIES_DIRECTORY_NAME = 'similarities'
image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
directory = None
duplicates_directory = None
similarities_directory = None

def select_directory():
    global directory
    global duplicates_directory
    global similarities_directory
    
    directory = filedialog.askdirectory()
    if directory:
        selected_dir_label.config(text=directory)
        duplicates_directory = os.path.join(directory, DUPLICATES_DIRECTORY_NAME)
        similarities_directory = os.path.join(directory, SIMILARITIES_DIRECTORY_NAME)

def hash_file(filename):
    with open(filename , "rb") as file:
        bytes = file.read()
        filehash = hashlib.sha256(bytes).hexdigest()
        return filehash

def get_images_in_directory(directory):
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
    images = [os.path.join(directory, file) for file in os.listdir(directory) if file.lower().endswith(image_extensions)]
    
    return images

def move_duplicate_images():
    if not directory:
        return

    image_hashes = {}

    images = get_images_in_directory(directory)

    if not os.path.exists(duplicates_directory):
        os.makedirs(duplicates_directory)

    for img in images:
        hash = hash_file(img)
        if hash in image_hashes:
            filename = os.path.basename(img)
            newPath = os.path.join(duplicates_directory, filename)
            os.rename(img, newPath)
        else:
            image_hashes[hash] = img
    
    if len(os.listdir(duplicates_directory)) == 0:
        os.rmdir(duplicates_directory)
    
    move_similar_images()

def move_similar_images():
    if not directory:
        return
    
    image_names = get_images_in_directory(directory)
    model = SentenceTransformer('clip-ViT-B-32')

    encoded_image = model.encode([Image.open(filepath) for filepath in image_names], batch_size=128, convert_to_tensor=True, show_progress_bar=True)

    # Now we run the clustering algorithm. This function compares images aganist 
    # all other images and returns a list with the pairs that have the highest 
    # cosine similarity score
    processed_images = util.paraphrase_mining_embeddings(encoded_image)

    #duplicates = [image for image in processed_images if image[0] >= 0.999]
    for score, image_id1, image_id2 in processed_images:
        print("\nScore: {:.3f}%".format(score * 100))
        print(image_names[image_id1])
        print(image_names[image_id2])



root = Tk()
root.title('PicPrune')
root.minsize(width=800, height=500)
frm = ttk.Frame(root, padding=10)

frm.grid()
ttk.Label(frm, text="Select image directory: ").grid(column=0, row=0)
ttk.Button(frm, text="->", command=select_directory).grid(column=1, row=0)
selected_dir_label = ttk.Label(frm, text="")
selected_dir_label.grid(column=0, row=1, columnspan=2, sticky="nsew")

ttk.Button(frm, text='Proceed', command=move_duplicate_images).grid(column=0, row=2, columnspan=2, sticky='nsew')

root.mainloop()