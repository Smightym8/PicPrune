# PicPrune

PicPrune is a simple tool to remove duplicate images from a directory. 
It uses a perceptual hash to compare images and remove duplicates. It is written in Python and uses the OpenCV library. 

This project is developed for the ÖH Hackathon 2024. Thanks to [Essiga](https://github.com/Essiga) for organizing the event.

## How to contribute
Install conda and create a new environment with the dependencies of this project:
```bash
conda env create -f environment.yml
```

Activate the environment:
```bash
conda activate PicPrune
```

If you have an existing conda environment run the following command to update it with the dependencies of this project:
```bash
conda env update --file environment.yml --prune
```

If you add any packages to the environment, update the environment.yml file with the following command:
```bash
conda env export --from-history > environment.yml
```

After exporting the environment remove the prefix in the `environment.yml` file.
