# Script to read url logfiles and return most frequent urls listed in logfiles, set to read multiple log files at a time using a url supplied by argument

import sys
import re
from collections import Counter
from urllib.request import urlopen

#Function to strip all urls from the logfile ignoring any other verbiage
def extract_urls(text):
    """Extract URLs from text using regex"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

#main function
def main():
    #Throw an error if no url is supplied. Can't download anything if we don't know where it is
    if len(sys.argv) < 2:
        print("Usage: python urlProcess.py <log_file_url> [log_file_url2] ...")
        sys.exit(1)
    
    #Define the url dictionary we'll be adding all urls from across supplied logs
    all_urls = []
    
    #For each url supplied, open it, read the content, make sure it's text format and downloadable or raise an error. 
    #Add any URLs present to the dictionary.
    for log_url in sys.argv[1:]:
        try:
            with urlopen(log_url) as response:
                content = response.read().decode('utf-8')
                urls = extract_urls(content)
                all_urls.extend(urls)
        except Exception as e:
            print(f"Error downloading {log_url}: {e}")
    
    #End if no URLs have been added to the dictionary.
    if not all_urls:
        print("No URLs found")
        return
    
    #Count occurrences
    url_counts = Counter(all_urls)
    
    #Sort by frequency (descending)
    for url, count in url_counts.most_common():
        print(f"{url} is the most common with {count} occurrences")

if __name__ == "__main__":
    main()