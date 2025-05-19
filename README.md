# excel-crawler

## How to Run

1. **Set up your environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. **Run the script sequence**:

   You must first run `read-file.py`, which reads names from the Excel file and prepares them for the crawler. Then, run `crawl.py` to perform the image search and download.

   ```bash
   python read-file.py
   ```

## Notes

- Ensure you have Python 3.7+ installed.
- `read-file.py` reads from the Excel file and feeds the names to `crawl.py`.
- `crawl.py` performs the image crawling using the keywords provided.
