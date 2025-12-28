import requests
from bs4 import BeautifulSoup
import re

url = "https://novelfull.net/a-will-eternal.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

main_list = soup.find(id='list-chapter')
if main_list:
    links = main_list.find_all('a')
    print(f"Total links in #list-chapter: {len(links)}")
    for l in links:
        text = l.get_text(strip=True)
        href = l.get('href')
        # Check if it looks like a pagination link (single digit or 'Next')
        is_pagination = False
        if text.isdigit() or text in ['Next', 'Last', 'First', 'Prev', '<', '>', '<<', '>>']:
            is_pagination = True
            
        print(f"Link: '{text}' | Pag: {is_pagination}")
else:
    print("No #list-chapter found")
