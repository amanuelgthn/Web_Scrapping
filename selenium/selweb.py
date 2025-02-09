#!/usr/bin/env python3
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from pandas import DataFrame, ExcelWriter  # Import pandas for saving the results in Excel
from sys import argv

# List of US states
us_states = [
    "Alabama"
]
us_states = us_states[::-1]
print("US States:", us_states)

# Set up Chrome options (and proxy if needed)
chrome_options = webdriver.ChromeOptions()
service = Service(ChromeDriverManager().install())

# Uncomment and update these lines if you wish to use a proxy.
# proxy = 'http://51.158.68.133:8811'
# options = {
#     'proxy': {
#         'http': proxy,
#         'https': proxy,
#         'no_proxy': 'localhost,127.0.0.1'
#     }
# }

# Initialize the driver once outside the loop
driver = webdriver.Chrome(
    service=service, 
    options=chrome_options,
    # seleniumwire_options=options
)

def scroll_feed(driver):
    """Scrolls the feed until no new results are loaded."""
    scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
    last_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_div)
    while True:
        driver.execute_script("arguments[0].scrollBy(0, 1000);", scrollable_div)
        time.sleep(2)  # Wait for new results to load
        new_height = driver.execute_script("return arguments[0].scrollHeight;", scrollable_div)
        if new_height == last_height:
            break
        last_height = new_height

# Create an Excel writer object that will write all state sheets to one file.
with ExcelWriter('resultsusa.xlsx', engine='openpyxl') as writer:
    # Loop through each state
    for state in us_states:
        try:
            # Create the search keyword (e.g., "ecommerce California")
            keyword = "ecommerce " + state
            driver.get(f'https://www.google.com/maps/search/{keyword}/')

            # Attempt to close any initial popup if it appears
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))
                ).click()
            except Exception:
                pass

            # Wait for the feed container to load
            scrollable_div = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )

            # Scroll through the feed to load more items
            scroll_feed(driver)

            # Extract the individual listing items
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
                    # Example: "4.7 star rating · 123 reviews"
                    rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") 
                                      if piece.replace(",", ".").replace(".", "", 1).isdigit()]
                    if rating_numbers:
                        data['stars'] = rating_numbers[0]
                        data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else 0
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

                # Extract email and LinkedIn from the business website if available.
                # Instead of cancelling the whole search on error, we catch exceptions here
                if data.get('website'):
                    current_tab = driver.current_window_handle
                    # Open a new tab to load the website
                    driver.execute_script("window.open('');")
                    new_tab = [handle for handle in driver.window_handles if handle != current_tab][0]
                    driver.switch_to.window(new_tab)
                    try:
                        # Set a page load timeout (adjust as needed)
                        driver.set_page_load_timeout(60)
                        driver.get(data['website'])
                        time.sleep(5)  # Wait for the website to load; adjust as necessary.
                        page_source = driver.page_source

                        # Use regex to search for an email address
                        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', page_source)
                        data['email'] = emails[0] if emails else None

                        # Use regex to search for a LinkedIn URL
                        linkedin_urls = re.findall(r'https?://(?:www\.)?linkedin\.com/[^\s"\']+', page_source)
                        data['linkedin'] = linkedin_urls[0] if linkedin_urls else None

                    except Exception as e:
                        # Instead of cancelling the entire process, log the error and set fields to None
                        print(f"Error extracting email/LinkedIn from website for state {state}: {e}")
                        data['email'] = None
                        data['linkedin'] = None
                    finally:
                        try:
                            driver.close()  # Close the new tab
                        except Exception as close_e:
                            print(f"Error closing tab: {close_e}")
                        driver.switch_to.window(current_tab)
                else:
                    data['email'] = None
                    data['linkedin'] = None

                if data.get('title'):
                    results.append(data)

            # Create a DataFrame for this state's results and write it to its own sheet.
            df = DataFrame(results)
            # Excel sheet names are limited to 31 characters. We use the state name (or a trimmed version).
            sheet_name = state[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Results for {state} written to sheet '{sheet_name}'.")
            # Clear results for the next state
            results.clear()

        except Exception as state_err:
            print(f"Error processing state {state}: {state_err}")

# The Excel file with all sheets is automatically saved when exiting the 'with' block.

# Finally, close the driver
driver.quit()
print("All states processed and Excel file 'resultsusa.xlsx' has been created successfully!")
