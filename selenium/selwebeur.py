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

# List of Belgium cities
belgium_cities = [
    "Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges", "Namur",
    "Leuven", "Mons", "Aalst", "Mechelen", "Ostend", "Tournai", "Hasselt",
    "Sint-Niklaas", "Dendermonde", "Roeselare", "Kortrijk", "Genk", "Seraing",
    "Turnhout", "Herstal", "Virton", "Verviers", "Maaseik", "Waremme", "Andenne",
    "Thuin", "Enghien", "Bergen", "Sint-Truiden", "Diksmuide", "Blankenberge",
    "La Louvière"
]

print("Belgium Cities:", belgium_cities)

# Set up Chrome options
chrome_options = webdriver.ChromeOptions()
service = Service(ChromeDriverManager().install())

# Initialize the driver
driver = webdriver.Chrome(service=service, options=chrome_options)

def scroll_feed(driver, scroll_pause=2, max_attempts=3):
    """
    Scrolls the results feed until no new results are loaded.
    It scrolls to the bottom of the feed repeatedly and waits for the lazy-loading to finish.
    If after max_attempts no new height is detected, it stops scrolling.
    """
    # Wait until the feed is available
    feed = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
    )
    last_height = driver.execute_script("return arguments[0].scrollHeight;", feed)
    attempts = 0
    while attempts < max_attempts:
        # Scroll to the bottom of the feed container
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", feed)
        time.sleep(scroll_pause)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", feed)
        if new_height == last_height:
            attempts += 1
        else:
            attempts = 0
            last_height = new_height

# List to collect all data frames
all_data_frames = []

# Loop through each city
for city in belgium_cities:
    try:
        keyword = "ecommerce " + city
        driver.get(f'https://www.google.com/maps/search/{keyword}/')

        # Attempt to close any initial popup
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))
            ).click()
        except Exception:
            pass

        # Wait for the feed container to load and then scroll through the feed
        scroll_feed(driver)

        # Extract listing items from the feed
        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
        results = []

        for item in items:
            data = {}

            # Extract basic details
            try:
                data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
            except Exception:
                data['title'] = None

            try:
                data['link'] = item.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            except Exception:
                data['link'] = None

            try:
                data['website'] = item.find_element(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction] div > a').get_attribute('href')
            except Exception:
                data['website'] = None

            try:
                rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
                rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split() 
                                  if piece.replace(",", ".").replace(".", "", 1).isdigit()]
                data['stars'] = rating_numbers[0] if rating_numbers else None
                data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else None
            except Exception:
                data['stars'] = None
                data['reviews'] = None

            try:
                text_content = item.text
                phone_pattern = r'([0-9\+\-\(\) ]{8,})'
                matches = re.findall(phone_pattern, text_content)
                phone_numbers = list(set(matches))
                data['phone'] = phone_numbers[0] if phone_numbers else None
            except Exception:
                data['phone'] = None

            # Extract email and LinkedIn from the website if available
            data['email'] = None
            data['linkedin'] = None
            if data.get('website'):
                current_tab = driver.current_window_handle
                driver.execute_script("window.open('');")
                new_tab = [h for h in driver.window_handles if h != current_tab][0]
                driver.switch_to.window(new_tab)
                try:
                    driver.set_page_load_timeout(60)
                    driver.get(data['website'])
                    time.sleep(5)
                    page_source = driver.page_source
                    emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', page_source)
                    data['email'] = emails[0] if emails else None
                    linkedin_urls = re.findall(r'https?://(?:www\.)?linkedin\.com/[^\s"\']+', page_source)
                    data['linkedin'] = linkedin_urls[0] if linkedin_urls else None
                except Exception as e:
                    print(f"Error extracting data from {data['website']}: {e}")
                finally:
                    driver.close()
                    driver.switch_to.window(current_tab)

            if data.get('title'):
                results.append(data)

        # Create a DataFrame for the current city if results exist
        if results:
            df = pd.DataFrame(results)
            new_df = pd.DataFrame({
                'Company Name': df['title'],
                'Contact Name': '',
                'Email': df['email'],
                'Job Position': '',
                'Mobile': df['phone'],
                'Website': df['website'],
                'LinkedIn': df['linkedin'],
                'City': city
            })
            all_data_frames.append(new_df)
            print(f"Processed {city} with {len(df)} entries.")
        else:
            print(f"No data found for {city}.")

    except Exception as e:
        print(f"Error processing {city}: {e}")

# Combine all data frames and save to Excel
if all_data_frames:
    combined_df = pd.concat(all_data_frames, ignore_index=True)
    with pd.ExcelWriter('resultsbelgium.xlsx') as writer:
        combined_df.to_excel(writer, sheet_name='All Cities', index=False)
    print("All data saved to 'resultsbelgium.xlsx' in sheet 'All Cities'.")
else:
    print("No data collected from any city.")

# Close the driver
driver.quit()
