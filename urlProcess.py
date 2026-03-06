import sys
import re
from collections import Counter
from urllib.request import urlopen

def extract_urls(text):
    """Extract URLs from text using regex"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scratch.py <log_file_url> [log_file_url2] ...")
        sys.exit(1)
    
    all_urls = []
    
    for log_url in sys.argv[1:]:
        try:
            with urlopen(log_url) as response:
                content = response.read().decode('utf-8')
                urls = extract_urls(content)
                all_urls.extend(urls)
        except Exception as e:
            print(f"Error downloading {log_url}: {e}")
    
    if not all_urls:
        print("No URLs found")
        return
    
    # Count occurrences
    url_counts = Counter(all_urls)
    
    # Sort by frequency (descending)
    for url, count in url_counts.most_common():
        print(f"{url} is the most common with {count} occurrences")

if __name__ == "__main__":
    main()