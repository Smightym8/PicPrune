import customtkinter
from tkinter import filedialog
import hashlib
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import os
from collections import defaultdict


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.minsize(width=800, height=500)
        self.title("PicPrune")

        self.directory = None
        self.duplicates_directory = None
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

        self.label = customtkinter.CTkLabel(self, text="PicPrune", font=("Ubuntu", 36))
        self.label.pack(padx=20, pady=20)

        self.button = customtkinter.CTkButton(self, text="Select image directory", command=self.select_directory)
        self.button.pack(padx=20, pady=20)

        self.label2 = customtkinter.CTkLabel(self, text=f"Selected directory: {self.directory}", font=("Ubuntu", 12))
        self.label2.pack()

        self.filter_button = customtkinter.CTkButton(self, text="Filter images", command=self.process_images)
        self.filter_button.pack(padx=20, pady=20)

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        self.label2.configure(text=f"Selected directory: {self.directory}")
        self.duplicates_directory = os.path.join(self.directory, "duplicates")

    def process_images(self):
        if not self.directory:
            print("No directory selected")
            return

        print("Processing images")
        self.filter_duplicate_images()
        self.filter_similar_images()
        print("Finished processing images")

    def filter_duplicate_images(self):
        image_hashes = {}
        images = self.get_images_in_directory()

        if not os.path.exists(self.duplicates_directory):
            os.makedirs(self.duplicates_directory)

        for img in images:
            hash = self.hash_file(img)
            if hash in image_hashes:
                filename = os.path.basename(img)
                new_path = os.path.join(self.duplicates_directory, filename)
                os.rename(img, new_path)
            else:
                image_hashes[hash] = img

        if len(os.listdir(self.duplicates_directory)) == 0:
            os.rmdir(self.duplicates_directory)

    def filter_similar_images(self):
        image_names = self.get_images_in_directory()
        model = SentenceTransformer('clip-ViT-B-32')

        encoded_image = model.encode([Image.open(filepath) for filepath in image_names], batch_size=128,
                                     convert_to_tensor=True, show_progress_bar=True)

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
                new_path = os.path.join(self.directory, f'{cluster_id}_{os.path.basename(img_path)}')
                os.rename(img_path, new_path)

    def get_images_in_directory(self):
        images = [os.path.join(self.directory, file) for file in os.listdir(self.directory) if
                  file.lower().endswith(self.image_extensions)]

        return images

    @staticmethod
    def hash_file(filename):
        with open(filename, "rb") as file:
            bytes = file.read()
            filehash = hashlib.sha256(bytes).hexdigest()
            return filehash


if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    app = App()
    app.mainloop()