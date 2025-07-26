import os
from PIL import Image

def resize_pngs_in_folder(folder_path, size=(1200, 1500), output_folder=None):
    """
    Resizes all PNG images in the specified folder to the given size.
    
    Parameters:
        folder_path (str): Path to the folder containing PNG images.
        size (tuple): Target size (width, height). Default is (1200, 1200).
        output_folder (str): Optional. If provided, saves resized images to this folder.
                             Otherwise, overwrites the originals.
    """
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.png'):
            image_path = os.path.join(folder_path, filename)
            with Image.open(image_path) as img:
                resized_img = img.resize(size, Image.LANCZOS)
                save_path = os.path.join(output_folder or folder_path, filename)
                resized_img.save(save_path)
                print(f"Resized and saved: {save_path}")

def main():
    input_folder = "data/team_logos"         # <-- Replace with your folder path
    output_folder = "data/team_logos"      # <-- Optional: replace or set to None
    resize_pngs_in_folder(input_folder, size=(1200, 1550), output_folder=output_folder)

if __name__ == "__main__":
    main()
