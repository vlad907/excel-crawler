import re
import os
import sys
import requests
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import hashlib
import logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("selenium").setLevel(logging.ERROR)


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

def download_images_google(query, folder_name, base_name, num_images=10):
    from urllib.parse import quote

    folder_name = sanitize_filename(folder_name)
    base_name = sanitize_filename(base_name)
    logging.info(f"Creating folder: {folder_name}, base name: {base_name}")
    os.makedirs(folder_name, exist_ok=True)

    hash_log_path = os.path.join(folder_name, "image_hashes.txt")
    if os.path.exists(hash_log_path):
        with open(hash_log_path, "r") as f:
            seen_hashes = set(line.strip() for line in f.readlines())
    else:
        seen_hashes = set()

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.google.com/search?hl=en&gl=us&tbm=isch&q={quote(query)}"
        driver.get(search_url)
        logging.info(f"Page loaded: {driver.current_url}")
        logging.info("Waiting for thumbnails to load...")
        try:
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(),'Accept all') or contains(text(),'I agree')]]"))
            )
            consent_button.click()
            time.sleep(2)
        except Exception:
            pass

        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            visible = driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
            logging.info(f"Scroll {i+1}: Found {len(visible)} thumbnails so far...")

        try:
            WebDriverWait(driver, 20).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")) > 5
            )
        except Exception:
            logging.warning("Timeout waiting for image thumbnails.")
            logging.warning("Thumbnails still not visible after scroll.")
            first_10_imgs = driver.find_elements(By.TAG_NAME, "img")[:10]
            for img in first_10_imgs:
                print("IMG TAG:", img.get_attribute("outerHTML")[:200])
            return
        thumbs = driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
        if not thumbs:
            logging.warning("No thumbnails found.")
            return

        for i, thumb in enumerate(thumbs[:num_images]):
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", thumb)
                thumb.click()
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img.n3VNCb")))
                imgs = driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and src.startswith("http") and "gstatic" not in src:
                        logging.info(f"Image source: {src}")
                        response = requests.get(src, timeout=5)
                        if response.status_code == 200:
                            img_data = response.content
                            img_obj = Image.open(BytesIO(img_data))
                            if img_obj.width >= 300 and img_obj.height >= 300:
                                new_hash = hashlib.sha256(img_data).hexdigest()
                                if new_hash in seen_hashes:
                                    logging.info(f"Skipped previously downloaded image (hash match): {base_name}_{i+1}.jpg")
                                    break
                                filename = os.path.join(folder_name, f"{base_name}_{i+1}.jpg")
                                if os.path.exists(filename):
                                    with open(filename, "rb") as existing_file:
                                        existing_hash = hashlib.sha256(existing_file.read()).hexdigest()
                                    if existing_hash == new_hash:
                                        logging.info(f"Skipped identical image (hash match): {filename}")
                                        break
                                    else:
                                        os.remove(filename)
                                        logging.info(f"Overwriting image due to hash mismatch: {filename}")
                                with open(filename, "wb") as f:
                                    f.write(img_data)
                                with open(hash_log_path, "a") as hash_file:
                                    hash_file.write(new_hash + "\n")
                                seen_hashes.add(new_hash)
                                logging.info(f"Saved image to {filename} ({img_obj.width}x{img_obj.height})")
                                break
                time.sleep(random.uniform(1, 2.5))
            except Exception as e:
                logging.warning(f"Failed to download image {i+1}: {e}")
    finally:
        driver.quit()

# New function: download_documents
def download_documents(query, folder_name, base_name, num_docs=10):
    from urllib.parse import quote
    from bs4 import BeautifulSoup

    folder_name = sanitize_filename(folder_name)
    base_name = sanitize_filename(base_name)
    print(f"Creating folder: {folder_name}, base name: {base_name}")
    os.makedirs(folder_name, exist_ok=True)

    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.google.com/search?q={quote(query + ' (filetype:pdf OR filetype:doc OR filetype:docx)')}"
        driver.get(search_url)
        try:
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//div[contains(text(),'Accept all') or contains(text(),'I agree')]]"))
            )
            consent_button.click()
            time.sleep(2)
        except Exception:
            pass
        print("Navigated to Google document results page...")
        time.sleep(2)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = [a['href'] for a in soup.find_all("a", href=True) if any(a['href'].lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx'])]
        seen = set()
        count = 0

        for i, link in enumerate(links):
            if link in seen or count >= num_docs:
                continue
            seen.add(link)
            try:
                response = requests.get(link, timeout=10)
                if response.status_code == 200:
                    ext = link.split('.')[-1].split('?')[0]
                    filename = os.path.join(folder_name, f"{base_name}_{count + 1}.{ext}")
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"Saved document: {filename}")
                    count += 1
                else:
                    print(f"Failed to download: {link} (Status {response.status_code})")
            except Exception as e:
                print(f"Error downloading {link}: {e}")
            time.sleep(random.uniform(1, 2))
    finally:
        driver.quit()

def download_images(query, folder_name, base_name, num_images=10):
    from urllib.parse import quote
    from ast import literal_eval

    folder_name = sanitize_filename(folder_name)
    base_name = sanitize_filename(base_name)
    print(f"Creating folder: {folder_name}, base name: {base_name}")
    os.makedirs(folder_name, exist_ok=True)

    hash_log_path = os.path.join(folder_name, "image_hashes.txt")
    if os.path.exists(hash_log_path):
        with open(hash_log_path, "r") as f:
            seen_hashes = set(line.strip() for line in f.readlines())
    else:
        seen_hashes = set()

    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.bing.com/images/search?q={quote(query)}"
        driver.get(search_url)
        print("Navigated to Bing image results page...")
        time.sleep(2)
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(1)

        thumbnails = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
        random.shuffle(thumbnails)
        thumbnails = thumbnails[:num_images]

        print(f"Found {len(thumbnails)} image containers.")

        for i, thumb in enumerate(thumbnails):
            try:
                m_json = thumb.get_attribute("m")
                if not m_json:
                    continue
                meta = literal_eval(m_json)
                src = meta.get("murl")
                if not src or not src.startswith("http"):
                    continue

                print(f"Image source: {src}")
                ext = "jpg"
                filename = os.path.join(folder_name, f"{base_name}_{i+1}.{ext}")

                for attempt in range(3):
                    try:
                        response = requests.get(src, timeout=5)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            if img.width >= 300 and img.height >= 300:
                                new_hash = hashlib.sha256(response.content).hexdigest()
                                if new_hash in seen_hashes:
                                    print(f"Skipped previously downloaded image (hash match): {filename}")
                                    break

                                if os.path.exists(filename):
                                    with open(filename, "rb") as existing_file:
                                        existing_hash = hashlib.sha256(existing_file.read()).hexdigest()
                                    if existing_hash == new_hash:
                                        print(f"Skipped identical image (hash match): {filename}")
                                        break
                                    else:
                                        os.remove(filename)
                                        print(f"Overwriting image due to hash mismatch: {filename}")
                                with open(filename, "wb") as f:
                                    f.write(response.content)
                                    with open(hash_log_path, "a") as hash_file:
                                        hash_file.write(new_hash + "\n")
                                    seen_hashes.add(new_hash)
                                print(f"Saved image to {filename} ({img.width}x{img.height})")
                                break
                            else:
                                print(f"Skipped low-res image ({img.width}x{img.height})")
                    except Exception as e:
                        if attempt == 2:
                            print(f"Failed to download {src} after 3 attempts: {e}")
                time.sleep(random.uniform(1, 2.5))
            except Exception as e:
                print(f"Failed to handle thumbnail {i+1}: {e}")
    finally:
        driver.quit()

def download_images_duckduckgo(query, folder_name, base_name, num_images=10):
    from bs4 import BeautifulSoup
    from urllib.parse import quote

    folder_name = sanitize_filename(folder_name)
    base_name = sanitize_filename(base_name)
    logging.info(f"Creating folder: {folder_name}, base name: {base_name}")
    os.makedirs(folder_name, exist_ok=True)

    hash_log_path = os.path.join(folder_name, "image_hashes.txt")
    if os.path.exists(hash_log_path):
        with open(hash_log_path, "r") as f:
            seen_hashes = set(line.strip() for line in f.readlines())
    else:
        seen_hashes = set()

    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://duckduckgo.com/?q={quote(query)}&t=h_&iax=images&ia=images"
        driver.get(search_url)
        logging.info(f"Page loaded: {driver.current_url}")
        time.sleep(2)

        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        image_elements = soup.find_all("img")
        logging.info(f"Found {len(image_elements)} image tags.")

        count = 0
        for img_tag in image_elements:
            from urllib.parse import urlparse, parse_qs, unquote

            src = img_tag.get("data-src") or img_tag.get("src")
            logging.debug(f"IMG HTML: {str(img_tag)[:200]}")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src

            # Extract actual image URL if wrapped by DuckDuckGo
            parsed = urlparse(src)
            if "duckduckgo.com/iu/" in src and "u" in parse_qs(parsed.query):
                real_url = unquote(parse_qs(parsed.query)["u"][0])
                logging.debug(f"Redirected image URL: {real_url}")
                src = real_url
            if not src.startswith("http"):
                continue
            logging.info(f"Image source: {src}")
            try:
                response = requests.get(src, timeout=5)
                if response.status_code == 200:
                    img_data = response.content
                    img_obj = Image.open(BytesIO(img_data))
                    if img_obj.width >= 300 and img_obj.height >= 300:
                        new_hash = hashlib.sha256(img_data).hexdigest()
                        if new_hash in seen_hashes:
                            logging.warning(f"Skipped duplicate image by hash: {src}")
                            continue
                        filename = os.path.join(folder_name, f"{base_name}_{count+1}.jpg")
                        if os.path.exists(filename):
                            with open(filename, "rb") as f:
                                existing_hash = hashlib.sha256(f.read()).hexdigest()
                            if existing_hash == new_hash:
                                logging.warning(f"Skipped identical file by hash: {filename}")
                                continue
                            else:
                                os.remove(filename)
                                logging.warning(f"Overwriting image due to hash mismatch: {filename}")
                        with open(filename, "wb") as f:
                            f.write(img_data)
                        with open(hash_log_path, "a") as hash_file:
                            hash_file.write(new_hash + "\n")
                        seen_hashes.add(new_hash)
                        logging.info(f"Saved image to {filename} ({img_obj.width}x{img_obj.height})")
                        count += 1
                        if count >= num_images:
                            break
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                logging.warning(f"Failed to download or validate {src}: {e}")
    finally:
        driver.quit()

def main():
    import itertools
    import json

    if len(sys.argv) != 3:
        print("Usage: python crawl.py <json_file_path> <num_images>")
        return

    json_file = sys.argv[1]
    if not os.path.exists(json_file):
        print(f"File not found: {json_file}")
        return

    try:
        num_images = int(sys.argv[2])
    except ValueError:
        print("Invalid number of images.")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            keywords = data.get("keywords", [])
            if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
                print(f"Invalid 'keywords' format in {json_file}")
                return
        except Exception as e:
            print(f"Error parsing {json_file}: {e}")
            return

    if not keywords:
        print(f"No keywords found in {json_file}")
        return

    base_folder = os.path.splitext(os.path.basename(json_file))[0]
    print(f"Processing JSON file: {base_folder}")
    keyword_cycle = itertools.cycle(keywords)

    for i in range(num_images):
        keyword = next(keyword_cycle)
        base_name = f"{base_folder}_{i+1}"
        print(f"Searching and downloading image for: {keyword}")
        download_images_duckduckgo(keyword, base_folder, base_name, 1)

if __name__ == "__main__":
    main()
def search_and_download_images(search_term, num_images, folder_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://www.google.com/imghp")

    box = driver.find_element(By.NAME, "q")
    box.send_keys(search_term)
    box.send_keys(Keys.RETURN)

    time.sleep(2)
    thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    count = 0
    for img in thumbnails:
        try:
            img.click()
            time.sleep(1)
            images = driver.find_elements(By.CSS_SELECTOR, "img.n3VNCb")
            for image in images:
                src = image.get_attribute("src")
                if src and "http" in src:
                    img_data = requests.get(src).content
                    with open(os.path.join(folder_path, f"{search_term}_{count+1}.jpg"), "wb") as handler:
                        handler.write(img_data)
                    count += 1
                    if count >= num_images:
                        break
            if count >= num_images:
                break
        except Exception:
            continue

    driver.quit()