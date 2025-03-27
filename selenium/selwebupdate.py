#!/usr/bin/env python3
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import pandas as pd
import requests
from requests.exceptions import RequestException
from extractfromtxt import extract_cities
from sys import argv

try: 
    keyword_var = " ".join(argv[1:])
except:
    keyword_var = 'ecommerce'
print(keyword_var)

print("Script is continuing...")

# Simulating the rest of your script
for i in range(3):
    print(f"Processing step {i+1}...")
cities = extract_cities("Classification.txt")
country_RealState = [
    "United Kingdom", "Japan", "India", "Brazil", "Canada",
    "Australia", "South Korea", "Russia"
]
NewCountry = {country: cities_list for country, cities_list in cities.items() if country.replace("_cities", "").capitalize() in country_RealState}
print("NewCountry: {}".format(NewCountry.keys()))

# Precompile regex patterns
PHONE_REGEX = re.compile(r'([0-9\+\-\(\) ]{8,})')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b(?!.*\.(png|jpg|jpeg|gif|bmp))')
LINKEDIN_REGEX = re.compile(r'https?://(?:www\.)?linkedin\.com/[^\s"\']+')
NAME_REGEX = re.compile(r'([A-Z][a-z]+ [A-Z][a-z]+)')  # Simple regex for names
JOB_TITLE_REGEX = re.compile(r'\b(CEO|Founder|Manager|Director|Engineer|Developer|President)\b', re.IGNORECASE)

# Configure headless browser
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
prefs = {'profile.default_content_setting_values': {'images': 2}}
chrome_options.add_experimental_option('prefs', prefs)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def scroll_feed(driver):
    """Scrolls the feed until no new results are loaded."""
    scrollable_div = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
    )
    items_selector = 'div[role="feed"] > div > div[jsaction]'
    previous_count = len(driver.find_elements(By.CSS_SELECTOR, items_selector))
    attempts = 0

    while attempts < 5:
        driver.execute_script("arguments[0].scrollBy(0, 1000);", scrollable_div)
        time.sleep(1)
        current_count = len(driver.find_elements(By.CSS_SELECTOR, items_selector))
        if current_count > previous_count:
            previous_count = current_count
            attempts = 0
        else:
            attempts += 1

def extract_contact_info(url):
    """Extracts email, LinkedIn, contact name, and job position from a website."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        if response.status_code == 200:
            page_source = response.text
            emails = EMAIL_REGEX.findall(page_source)
            linkedin_urls = LINKEDIN_REGEX.findall(page_source)
            names = NAME_REGEX.findall(page_source)
            job_titles = JOB_TITLE_REGEX.findall(page_source)

            return (
                emails[0] if emails else None,
                linkedin_urls[0] if linkedin_urls else None,
                names[0] if names else None,
                job_titles[0] if job_titles else None
            )
    except RequestException as e:
        print(f"Request error for {url}: {e}")
    return (None, None, None, None)


for country, city_list in NewCountry.items():
    print("NEW COUNTRY EXTRACTIG")
    all_data = []
    print(f"Extracting data for {country} ...")
    
    for city in city_list:
        print(f"Extracting data for city {city} in {country} ...")
        try:
            keyword = f"{keyword_var} {city}"
            driver.get(f'https://www.google.com/maps/search/{keyword}/')

            try:
                WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))
                ).click()
            except Exception:
                pass

            scroll_feed(driver)
            items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
            
            for item in items:
                data = {'City': city}
                try:
                    data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
                    data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
                except Exception:
                    continue

                try:
                    data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
                except Exception:
                    data['website'] = None

                try:
                    rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
                    numbers = [float(piece.replace(",", ".")) for piece in rating_text.split() if piece.replace(",", ".").replace(".", "", 1).isdigit()]
                    data['stars'] = numbers[0] if numbers else None
                    data['reviews'] = int(numbers[1]) if len(numbers) > 1 else None
                except Exception:
                    data['stars'] = data['reviews'] = None

                try:
                    text_content = item.text
                    phone_match = PHONE_REGEX.search(text_content)
                    data['phone'] = phone_match.group(0) if phone_match else None
                except Exception:
                    data['phone'] = None

                if data['website']:
                    data['email'], data['linkedin'], data['contact_name'], data['job_position'] = extract_contact_info(data['website'])
                else:
                    data['email'], data['linkedin'], data['contact_name'], data['job_position'] = (None, None, None, None)

                all_data.append({
                    'Company Name': data.get('title'),
                    'Contact Name': data.get('contact_name'),
                    'Email': data.get('email'),
                    'Job Position': data.get('job_position'),
                    'Mobile': data.get('phone'),
                    'Website': data.get('website'),
                    'LinkedIn': data.get('linkedin'),
                    'City': city
                })

            print(f"Processed {city} with {len(items)} entries.")
        except Exception as e:
            print(f"Error processing {city}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        file_name = f"results_{country.replace(' ', '_')}_{keyword_var.replace(' ', '_')}.xlsx"
        with pd.ExcelWriter(file_name) as writer:
            df.to_excel(writer, index=False, sheet_name=country[:31])
        print(f"Data for {country} saved to '{file_name}'.")
    else:
        print(f"No data collected for {country}.")

driver.quit()

