import os
import re
import time
import random
import hashlib
import requests
from io import BytesIO
from PIL import Image
from urllib.parse import quote, urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import sys

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

def download_images_duckduckgo(query, folder_name, base_name, num_images=10, known_hashes=None, missing_indexes=None):
    folder_name = sanitize_filename(folder_name)
    base_name = sanitize_filename(base_name)
    os.makedirs(folder_name, exist_ok=True)

    # Determine existing indexes for append mode
    existing_indexes_set = set()
    for fname in os.listdir(folder_name):
        if fname.endswith(".jpg") and fname.startswith(base_name + "_"):
            rest = fname[len(base_name) + 1:]
            idx_str = rest.split("_", 1)[0].split(".", 1)[0]
            try:
                existing_indexes_set.add(int(idx_str))
            except ValueError:
                continue
    max_index = max(existing_indexes_set) if existing_indexes_set else 0

    hash_log_path = os.path.join(folder_name, "image_hashes.txt")
    seen_hashes = set()
    if os.path.exists(hash_log_path):
        with open(hash_log_path, "r") as f:
            seen_hashes.update(line.strip() for line in f)
    if known_hashes:
        seen_hashes.update(known_hashes)

    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(f"https://duckduckgo.com/?q={quote(query)}&t=h_&iax=images&ia=images")
        time.sleep(2)
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        image_elements = soup.find_all("img")

        count = 0
        # Determine how many images to download: missing slots or append count
        if missing_indexes is not None:
            total_needed = len(missing_indexes)
        else:
            total_needed = num_images
        for img_tag in image_elements:
            if count >= total_needed:
                break

            src = img_tag.get("data-src") or img_tag.get("src")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            parsed = urlparse(src)
            if "duckduckgo.com/iu/" in src and "u" in parse_qs(parsed.query):
                real_url = unquote(parse_qs(parsed.query)["u"][0])
                src = real_url
            if not src.startswith("http"):
                continue

            try:
                response = requests.get(src, timeout=5)
                if response.status_code == 200:
                    img_data = response.content
                    img_obj = Image.open(BytesIO(img_data))
                    if img_obj.width < 300 or img_obj.height < 300:
                        continue
                    new_hash = hashlib.sha256(img_data).hexdigest()
                    if new_hash in seen_hashes:
                        continue
                    # Determine the image index for naming
                    if missing_indexes:
                        idx = missing_indexes[count]
                    else:
                        # Append after the highest existing index
                        idx = max_index + count + 1
                    # Use a sequence suffix to follow the existing "_<index>_<seq>.jpg" schema
                    seq = 1
                    filename = os.path.join(folder_name, f"{base_name}_{idx}_{seq}.jpg")
                    with open(filename, "wb") as f:
                        f.write(img_data)
                    with open(hash_log_path, "a") as hf:
                        hf.write(new_hash + "\n")
                    seen_hashes.add(new_hash)
                    count += 1
            except Exception:
                continue
            time.sleep(random.uniform(1, 2))
    finally:
        driver.quit()

def rerun_for_directory(folder_name):
    hash_log_path = os.path.join(folder_name, "image_hashes.txt")
    if not os.path.exists(hash_log_path):
        print(f"No hash log found for {folder_name}, skipping.")
        return

    with open(hash_log_path, "r") as f:
        known_hashes = [line.strip() for line in f if line.strip()]

    # Use the folder name itself as the prefix for every image file
    base_name = os.path.basename(folder_name)

    # Scan the directory for existing images named like "<base_name>_<N>.jpg"
    existing_indexes = set()
    for fname in os.listdir(folder_name):
        if not (fname.endswith(".jpg") and fname.startswith(base_name + "_")):
            continue
        # Strip off the prefix "<base_name>_"
        rest = fname[len(base_name) + 1:]
        # Extract the number before the next "_" or "."
        idx_str = rest.split("_", 1)[0].split(".", 1)[0]
        try:
            idx = int(idx_str)
            existing_indexes.add(idx)
        except ValueError:
            continue

    # Figure out how many images there should be (one per hash), 
    # and compute which slots are missing
    total_hashes = len(known_hashes)
    expected_indexes = set(range(1, total_hashes + 1))
    missing_indexes = sorted(expected_indexes - existing_indexes)

    # Debug output
    print(f"Existing images: {sorted(existing_indexes)}")
    print(f"Expected images: {sorted(expected_indexes)}")
    print(f"Missing image indexes: {missing_indexes}")

    if not missing_indexes:
        print(f"No missing images in {folder_name}")
        return

    # Re-download just the missing slots
    print(f"Replacing {len(missing_indexes)} missing images in {folder_name}")
    download_images_duckduckgo(
        query=base_name,
        folder_name=folder_name,
        base_name=base_name,
        num_images=len(missing_indexes),
        known_hashes=known_hashes,
        missing_indexes=missing_indexes
    )

if __name__ == "__main__":
    json_dir = os.path.join(os.getcwd(), "json")
    # Determine selected JSON files
    if len(sys.argv) > 1:
        # Called with a JSON path or filename; use that directly
        arg = sys.argv[1]
        fname = os.path.basename(arg)
        selected_files = [fname]
    else:
        # Interactive JSON selection
        json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
        if not json_files:
            print("No JSON files found.")
            exit()
        print("Available JSON files:")
        for i, fname in enumerate(json_files, 1):
            print(f"{i}. {fname}")
        print("0. Run all")
        selection = input("Enter the number(s) of the JSON file(s) to process (e.g., 2 or 1-3 or 0 to run all): ").strip()
        if selection == "0":
            selected_files = json_files
        elif "-" in selection:
            start, end = map(int, selection.split("-"))
            selected_files = json_files[start-1:end]
        else:
            idx = int(selection)
            selected_files = [json_files[idx - 1]]

    # Ask whether to rerun missing images or append new ones
    operation = input("Enter 'r' to rerun missing images or 'a' to append new images: ").strip().lower()
    if operation not in ("r", "a"):
        print("Invalid operation, exiting.")
        sys.exit(1)
    append_count = None
    if operation == "a":
        append_count = int(input("How many images to append per JSON? ").strip())

    for filename in selected_files:
        folder_name = os.path.splitext(filename)[0]
        if operation == "r":
            print(f"Rerunning crawl for: {filename}")
            rerun_for_directory(folder_name)
        else:
            print(f"Appending images for: {filename}")
            # Read existing hashes
            hash_log_path = os.path.join(folder_name, "image_hashes.txt")
            existing_hashes = []
            if os.path.exists(hash_log_path):
                with open(hash_log_path, "r") as hf:
                    existing_hashes = [line.strip() for line in hf if line.strip()]
            # Download new images, appending to the folder
            download_images_duckduckgo(
                query=folder_name.replace("_", " "),
                folder_name=folder_name,
                base_name=folder_name,
                num_images=append_count,
                known_hashes=existing_hashes,
                missing_indexes=None
            )