#!/usr/bin/env python3
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import os

# Configure Chrome options for headless browsing
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
prefs = {'profile.default_content_setting_values': {'images': 2}}
chrome_options.add_experimental_option('prefs', prefs)

# Configure Selenium Wire to ignore unnecessary requests (optional)
seleniumwire_options = {
    'ignore_http_methods': ['HEAD', 'OPTIONS', 'POST'],
}

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(
    service=service,
    options=chrome_options,
    seleniumwire_options=seleniumwire_options
)

def scroll_page(driver, scroll_pauses=5):
    """Scrolls the page to trigger lazy-loaded content."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(scroll_pauses):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def download_mp3(url, download_dir):
    """Downloads an MP3 file from a URL."""
    try:
        filename = os.path.join(download_dir, url.split('/')[-1].split('?')[0])
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        
        # Skip if file already exists
        if os.path.exists(filename):
            print(f"Skipped {filename} (already exists)")
            return
        
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {filename}")
        else:
            print(f"Failed to download {url}: Status code {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Target URL containing MP3 files
TARGET_URL = 'https://orthodoxmezmur.com/'  # Replace with your target URL
DOWNLOAD_DIR = 'downloaded_mp3s'

# Create download directory
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

try:
    # Navigate to the target page
    driver.get(TARGET_URL)
    
    # Scroll to load all content
    scroll_page(driver)
    
    # Method 1: Capture MP3 URLs from network requests
    mp3_urls = set()
    for request in driver.requests:
        if request.response:
            content_type = request.response.headers.get('Content-Type', '').lower()
            if 'audio/mpeg' in content_type or request.url.lower().endswith('.mp3'):
                mp3_urls.add(request.url)
    
    # Method 2: Find MP3 links in page elements
    mp3_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href$=".mp3"]')
    for element in mp3_elements:
        href = element.get_attribute('href')
        if href:
            mp3_urls.add(href)
    
    # Download all unique MP3 files
    print(f"Found {len(mp3_urls)} MP3 files. Starting downloads...")
    for url in mp3_urls:
        download_mp3(url, DOWNLOAD_DIR)

finally:
    driver.quit()