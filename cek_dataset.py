import os

dataset_dir = 'dataset'
total_images = 0

print(f"--- Info Dataset ---")
for folder in sorted(os.listdir(dataset_dir)):
    folder_path = os.path.join(dataset_dir, folder)
    if os.path.isdir(folder_path):
        images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        count = len(images)
        total_images += count
        print(f"- {folder}: {count} gambar")

print(f"Total keseluruhan: {total_images} gambar")
print(f"--------------------")
