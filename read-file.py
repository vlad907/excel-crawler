import json
import crawl

import os
import subprocess

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Crawl new JSON file(s)")
    print("2. Rerun crawl for directories with missing/deleted images")

    mode = input("Enter 1 or 2: ").strip()

    if mode == "1":
        root_dir = os.path.dirname(os.path.abspath(__file__))
        json_dir = os.path.join(root_dir, "json")

        if not os.path.isdir(json_dir):
            print("No 'json' directory found.")
        else:
            json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
            if not json_files:
                print("No JSON files found.")
                exit()

            print("Available JSON files:")
            for i, fname in enumerate(json_files, 1):
                print(f"{i}. {fname}")
            print("0. Run all")

            selection = input("Enter the number(s) of the JSON file(s) to read (e.g., 2 or 1-3 or 0 to run all): ").strip()
            if selection == "0":
                selected_files = json_files
            elif "-" in selection:
                start, end = map(int, selection.split("-"))
                selected_files = json_files[start-1:end]
            else:
                idx = int(selection)
                selected_files = [json_files[idx - 1]]

            num_images = input("How many images do you want to download per file? ").strip()

            for filename in selected_files:
                file_path = os.path.join(json_dir, filename)
                print(f"Running crawl for: {filename}")
                try:
                    subprocess.run(["python", "crawl.py", file_path, num_images])
                except Exception as e:
                    print(f"Error running crawl.py for {filename}: {e}")

    elif mode == "2":
        root_dir = os.path.dirname(os.path.abspath(__file__))
        json_dir = os.path.join(root_dir, "json")

        if not os.path.isdir(json_dir):
            print("No 'json' directory found.")
            exit()
        json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
        if not json_files:
            print("No JSON files found.")
            exit()

        print("Available JSON files:")
        for i, fname in enumerate(json_files, 1):
            print(f"{i}. {fname}")
        print("0. Run all")

        selection = input("Enter the number(s) of the JSON file(s) to rerun (e.g., 2 or 1-3 or 0 to run all): ").strip()
        if selection == "0":
            selected_files = json_files
        elif "-" in selection:
            start, end = map(int, selection.split("-"))
            selected_files = json_files[start-1:end]
        else:
            idx = int(selection)
            selected_files = [json_files[idx - 1]]

        for filename in selected_files:
            file_path = os.path.join(json_dir, filename)
            print(f"Rerunning crawl for: {filename}")
            try:
                subprocess.run(["python", "rerun-crawl.py", file_path])
            except Exception as e:
                print(f"Error rerunning rerun-crawl.py for {filename}: {e}")
    else:
        print("Invalid selection.")
