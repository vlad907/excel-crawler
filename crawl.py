import os
import sys
import requests
from duckduckgo_search import DDGS

def download_images(query, folder_name, base_name, num_images=10):
    os.makedirs(folder_name, exist_ok=True)
    with DDGS() as ddgs:
        results = ddgs.images(query, max_results=num_images)
        for i, result in enumerate(results):
            image_url = result["image"]
            try:
                response = requests.get(image_url, timeout=5)
                if response.status_code == 200:
                    ext = image_url.split('.')[-1].split('?')[0]
                    if '/' in ext or len(ext) > 5:
                        ext = 'jpg'
                    filename = os.path.join(folder_name, f"{base_name}_{i+1}.{ext}")
                    with open(filename, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                print(f"Failed to download {image_url}: {e}")

def main():
    sheet_names = sys.argv[1:]
    if not sheet_names:
        print("No sheet names provided.")
        return

    print("Available sheet names:")
    print("0. Run on all")
    for i, name in enumerate(sheet_names, 1):
        print(f"{i}. {name}")
    
    try:
        choice = int(input("Enter the number of the sheet you want to search (or 0 to run all): "))
        num_images = int(input("How many images do you want to download per name? "))
        if choice == 0:
            for name in sheet_names:
                print(f"Searching and downloading images for: {name}")
                download_images(name, name, name, num_images)
        else:
            selected_name = sheet_names[choice - 1]
            print(f"Searching and downloading images for: {selected_name}")
            download_images(selected_name, selected_name, selected_name, num_images)
    except (IndexError, ValueError):
        print("Invalid selection.")

if __name__ == "__main__":
    main()