import requests
from bs4 import BeautifulSoup

url = "https://novelfull.net/a-will-eternal.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

main_list = soup.find(id='list-chapter')
if main_list:
    links = main_list.find_all('a')
    print(f"Found {len(links)} links in #list-chapter")
    for i, l in enumerate(links):
        print(f"{i}: Text='{l.get_text(strip=True)}' Href='{l.get('href')}'")
else:
    print("No #list-chapter found")
