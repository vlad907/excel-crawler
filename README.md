# excel-crawler

- web crawler that takes in cells of an excel file then creates keywords then uses thsese keywords to find
corresponding images.


## Using Gemini Tool

- Gemini tool helps build search keywords to use for crawling the web and finding corresponding images
- We make api calls to gemini and it will build a json file with a list of keywords

## How to Run

```bash

python gemini.py <excel file>
```


## How to Run

1. **Set up your environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the script**:

   You must first run `read-file.py`, which reads names from the Excel file and prepares them for the crawler.

   ```bash
   python read-file.py
   ```

## Notes

- Ensure you have Python 3.7+ installed.
- `read-file.py` reads from the Excel file and feeds the names to `crawl.py`.
- `crawl.py` performs the image crawling using the keywords provided.
- 'rerun-crawl.py' allows you to rerun crawl for images you want replaced as well as add more images to specified directory



