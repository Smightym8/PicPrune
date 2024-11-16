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

        self.title_font = customtkinter.CTkFont(family="Ubuntu", size=36)
        self.standard_text_font = customtkinter.CTkFont(family="Ubuntu", size=14)
        self.operation_font = customtkinter.CTkFont(family="Ubuntu", size=14)
        self.error_font = customtkinter.CTkFont(family="Ubuntu", size=14)

        self.directory = None
        self.duplicates_directory = None
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')

        self.label = customtkinter.CTkLabel(self, text="PicPrune", font=self.title_font)
        self.label.pack(padx=20, pady=20)

        self.button = customtkinter.CTkButton(self, text="Select image directory", font=self.standard_text_font, command=self.select_directory)
        self.button.pack(padx=20, pady=20)

        self.label2 = customtkinter.CTkLabel(self, text=f"Selected directory: {self.directory}", font=self.standard_text_font)
        self.label2.pack()

        self.filter_button = customtkinter.CTkButton(self, text="Filter images", font=self.standard_text_font, command=self.process_images)
        self.filter_button.pack(padx=20, pady=20)

        self.operation_label = customtkinter.CTkLabel(self, text="", font=self.operation_font)
        self.operation_label.pack(pady=(20, 5))

        self.progress_label = customtkinter.CTkLabel(self, text="Progress: 0%", font=self.standard_text_font)
        self.progress_label.pack(pady=(5, 5))

        self.progress_bar = customtkinter.CTkProgressBar(self, orientation="horizontal", mode="determinate")
        self.progress_bar.pack(padx=20, pady=20, fill="x")
        self.progress_bar.set(0)  # Initialize progress to 0

        self.error_label = customtkinter.CTkLabel(self, text="", font=self.error_font, text_color="red")
        self.error_label.pack(pady=10)

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            self.error_label.configure(text="")  # Clear error message
            self.label2.configure(text=f"Selected directory: {self.directory}")
            self.duplicates_directory = os.path.join(self.directory, "duplicates")
        else:
            self.label2.configure(text="Selected directory: None")

    def process_images(self):
        if not self.directory:
            self.error_label.configure(text="Error: No directory selected!")  # Display error in red
            return

        # Clear any previous error messages
        self.error_label.configure(text="")

        print("Processing images")
        self.operation_label.configure(text="Filtering duplicates...")
        self.progress_label.configure(text="Progress: 0%")
        self.progress_bar.set(0)

        self.filter_duplicate_images()

        self.operation_label.configure(text="Filtering similar images...")
        self.filter_similar_images()

        self.operation_label.configure(text="Finished processing images")
        self.progress_label.configure(text="Progress: 100%")
        self.progress_bar.set(1.0)
        print("Finished processing images")

    def filter_duplicate_images(self):
        image_hashes = {}
        images = self.get_images_in_directory()
        total_images = len(images)

        if not os.path.exists(self.duplicates_directory):
            os.makedirs(self.duplicates_directory)

        for idx, img in enumerate(images, start=1):
            hash = self.hash_file(img)
            if hash in image_hashes:
                filename = os.path.basename(img)
                new_path = os.path.join(self.duplicates_directory, filename)
                os.rename(img, new_path)
            else:
                image_hashes[hash] = img

            # Update progress
            progress = idx / total_images
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Progress: {int(progress * 100)}%")
            self.update_idletasks()  # Ensure UI updates in real-time

        if len(os.listdir(self.duplicates_directory)) == 0:
            os.rmdir(self.duplicates_directory)

    def filter_similar_images(self):
        image_names = self.get_images_in_directory()
        if not image_names:
            return

        total_steps = len(image_names) + 1  # Encoding + Clustering
        current_step = 0

        # Load the model
        model = SentenceTransformer('clip-ViT-B-32')
        current_step += 1
        self.update_progress_bar(current_step, total_steps)

        # Encode the images
        encoded_images = model.encode(
            [Image.open(filepath) for filepath in image_names],
            batch_size=128,
            convert_to_tensor=True,
            show_progress_bar=False  # Suppress internal progress bar
        )
        current_step += 1
        self.update_progress_bar(current_step, total_steps)

        # Perform paraphrase mining
        processed_images = util.paraphrase_mining_embeddings(encoded_images)
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

        self.update_progress_bar(total_steps, total_steps)  # Ensure progress bar reaches 100%

    def update_progress_bar(self, current_step, total_steps):
        progress = current_step / total_steps
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Progress: {int(progress * 100)}%")
        self.update_idletasks()

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
