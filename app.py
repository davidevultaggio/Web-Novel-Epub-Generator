import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from io import BytesIO
from ebooklib import epub
import re

# Set page configuration
st.set_page_config(page_title="Web Novel Downloader", page_icon="📚")

def get_chapters(url):
    """
    Fetches the URL and extracts chapter links.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return [], ""

    soup = BeautifulSoup(response.content, 'html.parser')
    
    chapters = []
    
    # Refined search: priority to specific ID 'list-chapter' which contains the full list
    # This avoids "Latest Chapters" section which is usually separate
    main_list = soup.find(id='list-chapter')
    
    if main_list:
        links = main_list.find_all('a')
        for link in links:
            title = link.get_text(strip=True)
            href = link.get('href')
            if href and title:
                # Filter out pagination links
                if title.isdigit() or title in ['Next', 'Prev', 'First', 'Last', 'Select page', '<', '>'] or any(x in title for x in ['<<', '>>', '»', '«']):
                    continue
                    
                if not href.startswith('javascript'):
                    if not href.startswith('http'):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    chapters.append({'Title': title, 'URL': href})
    else:
        # Fallback: Generic search for chapter lists if specific ID is missing
        potential_containers = soup.find_all(['ul', 'div'], class_=lambda c: c and any(x in c for x in ['list-chapter', 'chapter-list', 'chapters']))
        
        if potential_containers:
            for container in potential_containers:
                links = container.find_all('a')
                for link in links:
                    title = link.get_text(strip=True)
                    href = link.get('href')
                    if href and title:
                        if not href.startswith('javascript'):
                            if not href.startswith('http'):
                                from urllib.parse import urljoin
                                href = urljoin(url, href)
                            chapters.append({'Title': title, 'URL': href})

    novel_title = "Web Novel"
    if soup.title:
        novel_title = soup.title.get_text(strip=True).split('|')[0].strip()

    return chapters, novel_title

def download_chapter_content(url):
    """
    Downloads and cleans chapter content.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Heuristic to find content. 
        # Common IDs: chapter-content, content, divContent
        # Common Classes: chapter-content, entry-content
        content_div = soup.find(id='chapter-content')
        if not content_div:
            content_div = soup.find('div', class_='chapter-content')
        if not content_div:
             content_div = soup.find('div', class_='entry-content') # Wordpress standard
        if not content_div:
            # Fallback: find the div with the most p tags
            divs = soup.find_all('div')
            content_div = max(divs, key=lambda d: len(d.find_all('p'))) if divs else None

        if content_div:
            # Clean up
            for tag in content_div.find_all(['script', 'style', 'div']): # removing inner divs can be risky, but often they are ads
                # Check if div is nav
                if tag.name == 'div' and any(cls in (tag.get('class') or []) for cls in ['nav', 'navigation', 'ads']):
                    tag.decompose()
                elif tag.name in ['script', 'style']:
                    tag.decompose()
            
            # Remove purely navigation text/links usually at bottom
            for p in content_div.find_all('p'):
                text = p.get_text().lower()
                if 'prev chapter' in text or 'next chapter' in text:
                    p.decompose()

            return str(content_div)
            
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return f"<p>Error downloading chapter: {e}</p>"
    
    return "<p>Content not found</p>"

def create_epub(title, chapters_data, progress_bar):
    book = epub.EpubBook()
    book.set_identifier(f'id_{int(time.time())}')
    book.set_title(title)
    book.set_language('en')
    
    book.add_author('Unknown') # Could extract author if needed
    
    epub_chapters = []
    
    total_chapters = len(chapters_data)
    
    for i, chapter_info in enumerate(chapters_data):
        chap_title = chapter_info['Title']
        chap_url = chapter_info['URL']
        
        content = download_chapter_content(chap_url)
        
        c = epub.EpubHtml(title=chap_title, file_name=f'chap_{i+1}.xhtml', lang='en')
        c.content = f'<h1>{chap_title}</h1>{content}'
        
        book.add_item(c)
        epub_chapters.append(c)
        
        # Anti-ban sleep
        time.sleep(random.uniform(0.5, 1.5))
        
        # Update progress
        progress_bar.progress((i + 1) / total_chapters, text=f"Downloading: {chap_title}")
        
    # Define Table of Contents
    book.toc = (epub_chapters)
    
    # Add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style
    style = 'body { font-family: Times, serif; }'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)
    
    # Basic spine
    book.spine = ['nav'] + epub_chapters
    
    buffer = BytesIO()
    epub.write_epub(buffer, book, {})
    buffer.seek(0)
    return buffer

# App Layout
st.title("📚 Web Novel Downloader")
st.markdown("Enter the index page URL of a web novel to analyze its chapters.")

url_input = st.text_input("Novel URL", placeholder="Inserisci il link qui")
analyze_button = st.button("Analizza")

if "chapters" not in st.session_state:
    st.session_state["chapters"] = []
if "novel_title" not in st.session_state:
    st.session_state["novel_title"] = ""

if analyze_button and url_input:
    with st.spinner("Analyzing..."):
        chapters_data, title = get_chapters(url_input)
        
        if chapters_data:
            st.session_state["chapters"] = chapters_data
            st.session_state["novel_title"] = title
            st.success(f"Found {len(chapters_data)} chapters for '{title}'!")
        else:
            st.warning("No chapters found. Please check the URL or the site structure.")

if st.session_state["chapters"]:
    chapters_data = st.session_state["chapters"]
    title = st.session_state["novel_title"]
    
    st.write(f"Total Chapters: {len(chapters_data)}")
    
    df = pd.DataFrame(chapters_data)
    df.index = df.index + 1
    st.dataframe(df)
    
    custom_title = st.text_input("Nome del file ePub", value=title)
    
    if st.button("Scarica e Converti in ePub"):
        progress_bar = st.progress(0, text="Starting download...")
        
        try:
            epub_buffer = create_epub(custom_title, chapters_data, progress_bar)
            progress_bar.empty()
            st.success("Conversion complete!")
            
            st.download_button(
                label="Download ePub",
                data=epub_buffer,
                file_name=f"{custom_title}.epub",
                mime="application/epub+zip"
            )
        except Exception as e:
            st.error(f"An error occurred during creation: {e}")
