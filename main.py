from collections import defaultdict
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

def select_directory():
    global directory
    global duplicates_directory
    global similarities_directory
    
    directory = filedialog.askdirectory()
    if directory:
        selected_dir_label.config(text=directory)
        duplicates_directory = os.path.join(directory, DUPLICATES_DIRECTORY_NAME)
        similarities_directory = os.path.join(directory, SIMILARITIES_DIRECTORY_NAME)

def process_images():
    if not directory:
        return

    move_duplicate_images()
    move_similar_images()
    print("Finished processing images")

def hash_file(filename):
    with open(filename , "rb") as file:
        bytes = file.read()
        filehash = hashlib.sha256(bytes).hexdigest()
        return filehash

def get_images_in_directory(directory):
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

    images_to_remove = [image for image in processed_images if image[0] >= 0.9]

    clusters = defaultdict(set)

    # Populate the clusters dictionary
    for score, img1, img2 in images_to_remove:
        clusters[img1].add(img1)
        clusters[img1].add(img2)
        clusters[img2].add(img1)
        clusters[img2].add(img2)

    # Merge clusters that have common elements
    merged_clusters = []
    for cluster in clusters.values():
        for merged_cluster in merged_clusters:
            if not cluster.isdisjoint(merged_cluster):
                merged_cluster.update(cluster)
                break
        else:
            merged_clusters.append(cluster)

    # Prefix image names with the cluster id
    for cluster_id, cluster in enumerate(merged_clusters, start=1):
        for img_id in cluster:
            img_path = image_names[img_id]
            new_path = os.path.join(directory, f'{cluster_id}_{os.path.basename(img_path)}')
            os.rename(img_path, new_path)


root = Tk()
root.title('PicPrune')
root.minsize(width=800, height=500)
frm = ttk.Frame(root, padding=10)

frm.grid()
ttk.Label(frm, text="Select image directory: ").grid(column=0, row=0)
ttk.Button(frm, text="->", command=select_directory).grid(column=1, row=0)
selected_dir_label = ttk.Label(frm, text="")
selected_dir_label.grid(column=0, row=1, columnspan=2, sticky="nsew")

ttk.Button(frm, text='Proceed', command=process_images).grid(column=0, row=2, columnspan=2, sticky='nsew')

root.mainloop()