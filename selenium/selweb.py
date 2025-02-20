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


cities = extract_cities("Classification.txt")
# Precompile regex patterns for efficiency
PHONE_REGEX = re.compile(r'([0-9\+\-\(\) ]{8,})')
EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
LINKEDIN_REGEX = re.compile(r'https?://(?:www\.)?linkedin\.com/[^\s"\']+')

# List of Belgium cities



# Configure Chrome options for headless and efficiency
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
prefs = {'profile.default_content_setting_values': {'images': 2}}
chrome_options.add_experimental_option('prefs', prefs)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Headers for requests to mimic a real browser
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
    max_attempts = 5  # Adjust based on testing

    while attempts < max_attempts:
        driver.execute_script("arguments[0].scrollBy(0, 1000);", scrollable_div)
        time.sleep(1)  # Reduced sleep time
        current_count = len(driver.find_elements(By.CSS_SELECTOR, items_selector))
        if current_count > previous_count:
            previous_count = current_count
            attempts = 0
        else:
            attempts += 1

def extract_contact_info(url):
    """Extracts email and LinkedIn using requests."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=10)
        if response.status_code == 200:
            page_source = response.text
            emails = EMAIL_REGEX.findall(page_source)
            linkedin_urls = LINKEDIN_REGEX.findall(page_source)
            return (emails[0] if emails else None,
                    linkedin_urls[0] if linkedin_urls else None)
    except RequestException as e:
        print(f"Request error for {url}: {e}")
    return (None, None)

# List to collect all data
all_data = []
for country, list in cities.items():
    print("Exctracting data for {} ....".format(country))
    for city in list:
        print("Exctracting data {} city of {} ....".format(country, city))
        try:
            keyword = f"ecommerce {city}"
            driver.get(f'https://www.google.com/maps/search/{keyword}/')

            # Close initial popup if present
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

                # Extract title and link
                try:
                    data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
                    data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
                except Exception:
                    continue  # Skip if no title

                # Extract website
                try:
                    data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
                except Exception:
                    data['website'] = None

                # Extract rating and reviews
                try:
                    rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
                    numbers = [float(piece.replace(",", ".")) for piece in rating_text.split() 
                            if piece.replace(",", ".").replace(".", "", 1).isdigit()]
                    data['stars'] = numbers[0] if numbers else None
                    data['reviews'] = int(numbers[1]) if len(numbers) > 1 else None
                except Exception:
                    data['stars'] = data['reviews'] = None

                # Extract phone number
                try:
                    text_content = item.text
                    phone_match = PHONE_REGEX.search(text_content)
                    data['phone'] = phone_match.group(0) if phone_match else None
                except Exception:
                    data['phone'] = None

                # Extract email and LinkedIn
                data['email'], data['linkedin'] = extract_contact_info(data['website']) if data['website'] else (None, None)

                # Append cleaned data
                all_data.append({
                    'Company Name': data['title'],
                    'Contact Name': '',
                    'Email': data['email'],
                    'Job Position': '',
                    'Mobile': data['phone'],
                    'Website': data['website'],
                    'LinkedIn': data['linkedin'],
                    'City': city
                })

            print(f"Processed {city} with {len(items)} entries.")

        except Exception as e:
            print(f"Error processing {city}: {e}")

    # Save all data to Excel
    if all_data:
        df = pd.DataFrame(all_data)
        with pd.ExcelWriter('resultsALL.xlsx') as writer:
            df.to_excel(writer, index=False, sheet_name=str(country))
        print("Data saved to 'resultsbelgium.xlsx'.")
    else:
        print("No data collected.")

driver.quit()