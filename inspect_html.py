import requests
from bs4 import BeautifulSoup

url = "https://novelfull.net/a-will-eternal.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

print("--- Searching for specific IDs ---")
list_chapter_id = soup.find(id='list-chapter')
if list_chapter_id:
    print("Found element with id='list-chapter'")
    print(f"  Tag: {list_chapter_id.name}")
    print(f"  Classes: {list_chapter_id.get('class')}")
    # Check what kind of children it has
    children_uls = list_chapter_id.find_all('ul')
    print(f"  Contains {len(children_uls)} ul elements")
else:
    print("Did NOT find element with id='list-chapter'")

print("\n--- Searching for sections by header ---")
headers = soup.find_all(['h2', 'h3', 'h4', 'div'], string=lambda t: t and 'Latest' in t)
for h in headers:
    print(f"Found header: {h.name} - {h.get_text(strip=True)}")
    parent = h.parent
    if parent:
        print(f"  Parent: {parent.name} (Class: {parent.get('class')}, ID: {parent.get('id')})")

print("\n--- Listing all potential chapter lists ---")
uls = soup.find_all('ul', class_='list-chapter')
for i, ul in enumerate(uls):
    print(f"UL #{i}")
    # Try to identify based on preceding siblings or parents
    parent = ul.parent
    print(f"  Parent: {parent.name} (Class: {parent.get('class')}, ID: {parent.get('id')})")
    
    # Print first few links
    links = ul.find_all('a', limit=3)
    for l in links:
        print(f"    Link: {l.get_text(strip=True)}")
