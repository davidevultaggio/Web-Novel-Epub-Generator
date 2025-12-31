import streamlit as st
import requests
from bs4 import BeautifulSoup

import time
import random
from io import BytesIO
from ebooklib import epub
import re
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse

# Set page configuration
st.set_page_config(page_title="Web Novel Downloader", page_icon="📚")

def get_session():
    return requests.Session()

def get_chapters(url, status_callback=None):
    """
    Fetches the URL and extracts chapter links from all pages if pagination exists.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    session = get_session()
    all_chapters = []
    novel_title = "Web Novel"
    
    # 1. Fetch First Page
    if status_callback:
        status_callback("Analyzing page 1")
        
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return [], ""

    # Extract Title (Logic moved here using soup from first page)
    # Try to extract title from URL first for a cleaner name
    try:
        path = urlparse(url).path
        filename = path.split('/')[-1] # e.g., a-will-eternal.html
        slug = filename.rsplit('.', 1)[0] # a-will-eternal
        
        if slug and slug != "index": 
            clean_title = slug.replace('-', ' ').title()
            if len(clean_title) > 3:
                novel_title = clean_title
    except Exception as e:
        print(f"Error parsing URL for title: {e}")

    if novel_title == "Web Novel" and soup.title:
         novel_title = soup.title.get_text(strip=True).split('|')[0].strip()

    # 2. Function to extract chapters from a soup object
    def extract_from_soup(current_soup, base_url):
        chapters = []
        # Refined search: priority to specific ID 'list-chapter'
        main_list = current_soup.find(id='list-chapter')
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
                            href = urljoin(base_url, href)
                        chapters.append({'Title': title, 'URL': href})
        else:
             # Fallback
            potential_containers = current_soup.find_all(['ul', 'div'], class_=lambda c: c and any(x in c for x in ['list-chapter', 'chapter-list', 'chapters']))
            if potential_containers:
                for container in potential_containers:
                    links = container.find_all('a')
                    for link in links:
                        title = link.get_text(strip=True)
                        href = link.get('href')
                        if href and title:
                            if not href.startswith('javascript'):
                                if not href.startswith('http'):
                                    href = urljoin(base_url, href)
                                chapters.append({'Title': title, 'URL': href})
        return chapters

    # Extract from first page
    all_chapters.extend(extract_from_soup(soup, url))
    
    # 3. Pagination Logic
    last_page = 1
    pagination = soup.find('ul', class_='pagination') or soup.find(class_='pagination')
    
    if pagination:
        # Find all page numbers
        links = pagination.find_all('a')
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href')
            
            # Check for "Last"
            if 'Last' in text:
                # Try to extract page number from href (e.g. ?page=20 or page-20.html)
                # Helper: parse page param
                def get_page_num(url_str):
                    if not url_str: return 0
                    parsed = urlparse(url_str)
                    qs = parse_qs(parsed.query)
                    if 'page' in qs:
                        return int(qs['page'][0])
                    return 0
                
                num = get_page_num(href)
                if num > last_page:
                    last_page = num
            elif text.isdigit():
                num = int(text)
                if num > last_page:
                    last_page = num
    
    if last_page > 1:
        if status_callback:
            status_callback(f"Found {last_page} pages. Starting deep analysis...")
        
        # Determine base URL for pagination
        # NovelFull standard: ?page=X
        # We will append ?page=X to the user provided URL (or update it)
        
        parsed_url = urlparse(url)
        
        for p in range(2, last_page + 1):
             if status_callback:
                status_callback(f"Analyzing page {p}/{last_page}")
             
             # Construct URL
             # If query params exist, append or replace page
             query = parse_qs(parsed_url.query)
             query['page'] = [str(p)]
             new_query = urlencode(query, doseq=True)
             page_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
             
             try:
                 resp = session.get(page_url, headers=headers)
                 if resp.status_code == 200:
                     page_soup = BeautifulSoup(resp.content, 'html.parser')
                     new_chapters = extract_from_soup(page_soup, page_url)
                     
                     # Avoid duplicates if any
                     # (Simple check by URL)
                     existing_urls = set(c['URL'] for c in all_chapters)
                     for ch in new_chapters:
                         if ch['URL'] not in existing_urls:
                             all_chapters.append(ch)
                 
                 # Be polite
                 time.sleep(random.uniform(0.3, 0.7))
                 
             except Exception as e:
                 print(f"Error on page {p}: {e}")
                 # Continue to next page

    return all_chapters, novel_title

def download_chapter_content(url, chapter_title=None):
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

            # Remove the first element if it's the title
            # Refined removal logic:
            # 1. Strip leading empty elements
            # 2. Check for "Chapter X" patterns or fuzzy title matches
            # 3. Repeat until real content is found
            
            # Helper to check if text looks like a header/title
            def is_header_text(text, title):
                text = text.lower().strip()
                title = title.lower().strip()
                if not text: return True # Treat empty as "header to remove" to get to next
                
                # Check 1: Exact or fuzzy title match
                if title in text or (len(text) > 5 and text in title):
                    return True
                
                # Check 2: "Chapter N" pattern
                # Matches: "Chapter 1", "Chapter 1: Title", "Chapter 1 - Title"
                if re.match(r'^chapter\s+\d+', text):
                    return True
                    
                return False

            # Search in the first few elements (let's say top 5 to be safe)
            for _ in range(5):
                first_element = content_div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'])
                if not first_element:
                    break
                    
                text = first_element.get_text(strip=True)
                if is_header_text(text, chapter_title if chapter_title else ""):
                    first_element.decompose()
                else:
                    break

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
        
        content = download_chapter_content(chap_url, chap_title)
        
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

url_input = st.text_input("Novel URL", placeholder="Enter link here")
analyze_button = st.button("Analyze", type="primary")

if "chapters" not in st.session_state:
    st.session_state["chapters"] = []
if "novel_title" not in st.session_state:
    st.session_state["novel_title"] = ""

if analyze_button and url_input:
    # Use a container for status updates
    status_text = st.empty()
    
    def update_status(msg):
        status_text.text(msg)
        
    chapters_data, title = get_chapters(url_input, status_callback=update_status)
        
    if chapters_data:
        st.session_state["chapters"] = chapters_data
        st.session_state["novel_title"] = title
        status_text.empty() # Clear status

    else:
        status_text.empty()
        st.warning("No chapters found. Please check the URL or the site structure.")

if st.session_state["chapters"]:
    chapters_data = st.session_state["chapters"]
    title = st.session_state["novel_title"]
    
    st.divider()
    st.subheader("Selection & Download")
    
    total_found = len(chapters_data)
    st.write(f"Total chapters found: **{total_found}**")

    # Range Selection
    col1, col2 = st.columns(2)
    with col1:
        start_idx = st.number_input("From Chapter", min_value=1, max_value=total_found, value=1)
    with col2:
        end_idx = st.number_input("To Chapter", min_value=1, max_value=total_found, value=total_found)

    # Validate range
    if start_idx > end_idx:
        st.error("Start chapter cannot be greater than end chapter.")
        valid_range = False
    else:
        valid_range = True
        
    start_chapter_num = int(start_idx)
    end_chapter_num = int(end_idx)
    
    # Adjust list slicing (0-based)
    # User selects 1 to N
    # Slice is [0 : N] ? No, [0] is 1st. 
    # [start_idx-1 : end_idx]
    selected_chapters = chapters_data[start_chapter_num-1 : end_chapter_num]
    
    count_to_download = len(selected_chapters)
    
    auto_filename = f"{title}"
    
    if selected_chapters:
        # Auto-filename generation based on selection
        # Try to parse numbers from the actual First and Last selected chapter titles
        def extract_chapter_number(title):
            match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return None

        first_chap_title = selected_chapters[0]['Title']
        last_chap_title = selected_chapters[-1]['Title']
        
        first_num = extract_chapter_number(first_chap_title)
        last_num = extract_chapter_number(last_chap_title)
        
        if first_num is not None and last_num is not None:
             range_str = f" {first_num}-{last_num}"
        else:
             range_str = f" {start_idx}-{end_idx}" # Fallback to index
             
        auto_filename = f"{title}{range_str}"



    if st.button("Download and Convert to ePub" if valid_range else "Invalid Range", disabled=not valid_range, type="primary"):
        progress_bar = st.progress(0, text="Starting download...")
        
        try:
            epub_buffer = create_epub(auto_filename, selected_chapters, progress_bar)
            progress_bar.empty()
            st.success("Conversion complete!")
            
            st.download_button(
                label=f"Download {auto_filename}.epub",
                data=epub_buffer,
                file_name=f"{auto_filename}.epub",
                mime="application/epub+zip"
            )
        except Exception as e:
            st.error(f"An error occurred during creation: {e}")
