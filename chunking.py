import os
import requests
from bs4 import BeautifulSoup
import re

# 1. Configuration & Setup
URLS = [
    "https://www.reddit.com/r/ucla/comments/heshap/a_little_neuroscience_advice/",
    "https://www.reddit.com/r/ucla/comments/1tx4w7h/recommended_first_quarter_freshman_classes_for/",
    "https://www.reddit.com/r/ucla/comments/1siadcz/ucla_neuro_students_how_is_it/",
    "https://www.neurosci.ucla.edu/faculty/",
    "https://www.neurosci.ucla.edu/program/major-requirements/",
    "https://www.neurosci.ucla.edu/program/minor-requirements/",
    "https://www.neurosci.ucla.edu/program/major-capstone/",
    "https://www.bruinwalk.com/professors/natik-piri/all/",
    "https://www.bruinwalk.com/professors/william-grisham/",
    "https://www.bruinwalk.com/professors/stephanie-a-white/"
]

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# Set up directories
RAW_DIR = "./documents/raw/"
CLEAN_DIR = "./documents/clean/"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)

# Headers to mimic a browser (Crucial for Reddit & Bruinwalk)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 2. Core Functions
def fetch_and_save_raw(url, index):
    """Fetches HTML from a URL and saves it to the raw directory."""
    try:
        scrappable_url = url
        if "reddit.com" in url and "old.reddit.com" not in url:
            scrappable_url = url.replace("www.reddit.com", "old.reddit.com")

        response = requests.get(scrappable_url, headers=HEADERS, timeout=10)
        # response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        file_path = os.path.join(RAW_DIR, f"doc_{index}_raw.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_html_content(html_content):
    """Removes boilerplate, scripts, and extracts clean text."""
    if not html_content:
        return ""
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags completely
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript', 'meta']):
        element.decompose()
        
    # Extract text, separating elements with a space
    text = soup.get_text(separator=' ')
    
    # Clean up whitespace and leftover HTML entities
    # text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    # # text = text.replace('&amp;', '&').replace('&nbsp;', ' ')
    # text = text.replace('&amp;', '&').replace('&nbsp;', ' ')
    # REPLACE WITH THIS (Adds a regex to wipe compressed code/base64 strings):
    # Clean up whitespace and leftover HTML entities
    text = text.replace('&amp;', '&').replace('&nbsp;', ' ')

    # Remove long continuous blocks of character junk (CSS / Base64 strings)
    # This matches any sequence of non-whitespace characters longer than 60 characters
    text = re.sub(r'\S{60,}', '', text)

    # Wipe out common WordPress block editor terms often left behind
    text = re.sub(r'(\.tb-grid|\.wp-block|\.block-editor)[^{]*{[^}]*}', '', text)

    # Final sweep to compress all multiple whitespaces into single spaces
    text = re.sub(r'\s+', ' ', text)

    # Drop-in boilerplate phrase cleaner
    boilerplate_phrases = [
        "Skip to Main Content", 
        "Skip to content",
        "Main Navigation",
        "Toggle navigation"
    ]
    for phrase in boilerplate_phrases:
        text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)

    # Clean up any resulting double-spaces again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text.strip()

def chunk_text(text, chunk_size, overlap):
    """Splits text into chunks of specified size and overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# 3. Main Execution
if __name__ == "__main__":
    all_cleaned_documents = []
    all_chunks = []

    print("Starting Document Ingestion...\n")
    
    for i, url in enumerate(URLS, 1):
        print(f"Processing [{i}/{len(URLS)}]: {url}")
        
        # Step A: Load and save raw
        raw_html = fetch_and_save_raw(url, i)
        
        if raw_html:
            # Step B: Clean and save clean
            cleaned_text = clean_html_content(raw_html)
            clean_file_path = os.path.join(CLEAN_DIR, f"doc_{i}_clean.txt")
            
            with open(clean_file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
                
            all_cleaned_documents.append(cleaned_text)
            
            # Step C: Chunking
            doc_chunks = chunk_text(cleaned_text, CHUNK_SIZE, CHUNK_OVERLAP)
            all_chunks.extend(doc_chunks)

    # 4. Inspection & Verification
    print("\n" + "="*50)
    print("INSPECTION: Cleaned Document #5 (Major Requirements)")
    print("="*50)
    # Printing a snippet of the 5th document to verify cleaning worked
    if len(all_cleaned_documents) >= 5:
        print(all_cleaned_documents[4][:1500] + "...\n[TRUNCATED FOR READABILITY]")

    print("\n" + "="*50)
    print("INSPECTION: 5 Representative Chunks")
    print("="*50)
    
    # Print 5 chunks from the middle of the dataset to see varied content
    sample_chunks = all_chunks[len(all_chunks)//2 : len(all_chunks)//2 + 5]
    for idx, chunk in enumerate(sample_chunks, 1):
        print(f"--- Chunk {idx} (Length: {len(chunk)} chars) ---")
        print(chunk)
        print("-" * 50 + "\n")
        
    print(f"Pipeline complete! Total chunks generated: {len(all_chunks)}")