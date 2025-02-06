#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import re

@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    email: str = None
    social_media: dict = field(default_factory=dict)
    hours: dict = field(default_factory=dict)
    rating: float = None
    reviews: int = None
    category: str = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize((asdict(business) for business in self.business_list), sep="_")
    
    def save_to_excel(self, filename):
        self.dataframe().to_excel(f'{filename}.xlsx', index=False)
    
    def save_to_csv(self, filename):
        self.dataframe().to_csv(f'{filename}.csv', index=False)

def extract_hours(hours_text):
    hours_dict = {}
    if hours_text:
        for line in hours_text.split('\n'):
            if ':' in line:
                day, time = line.split(':', 1)
                hours_dict[day.strip()] = time.strip()
    return hours_dict

def main(search_for):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="cookies.json")
        page = context.new_page()

        page.goto('https://www.google.com/maps')
        
        try:
            page.locator("button:has-text('Zaakceptuj wszystko')").click()
        except:
            pass

        page.wait_for_selector('input#searchboxinput')
        page.fill('input#searchboxinput', search_for)
        page.keyboard.press('Enter')

        MAPS_PLACE_SELECTOR = "a[href^='https://www.google.com/maps/place/']"
        page.wait_for_selector(MAPS_PLACE_SELECTOR)
        anchors = page.locator(MAPS_PLACE_SELECTOR)
        count = anchors.count()
        print(f"Found {count} place anchors.")

        business_list = BusinessList()

        for i in range(min(count, 5)):
            anchor = anchors.nth(i)
            anchor.click()
            
            # Existing working selectors
            page.wait_for_selector('//div[@role="main"]//h1')
            business = Business()

            # Original fields (keep unchanged)
            try:
                business.name = page.locator('//h1[contains(@class, "fontHeadlineSmall")]').inner_text()
            except: pass

            try:
                business.address = page.locator('button[data-item-id="address"] div.fontBodyMedium').inner_text()
            except: pass

            try:
                business.website = page.locator('a[data-item-id="authority"] div.fontBodyMedium').inner_text()
            except: pass

            try:
                business.phone_number = page.locator('button[data-item-id^="phone:tel:"] div.fontBodyMedium').inner_text()
            except: pass

            # New lead generation features
            try:
                # Email extraction from website meta
                if business.website:
                    page.goto(business.website)
                    business.email = page.evaluate('''() => {
                        const meta = document.querySelector('meta[content*="@"]');
                        return meta ? meta.content : null;
                    }''')
                    page.go_back()
            except: pass

            try:
                # Social media links
                social = {}
                elements = page.locator('a[data-item-id*="social"]')
                for idx in range(elements.count()):
                    el = elements.nth(idx)
                    url = el.get_attribute('href')
                    label = el.get_attribute('aria-label').lower()
                    if 'facebook' in label: social['facebook'] = url
                    elif 'instagram' in label: social['instagram'] = url
                    elif 'twitter' in label: social['twitter'] = url
                    elif 'linkedin' in label: social['linkedin'] = url
                business.social_media = social
            except: pass

            try:
                # Business hours
                hours_btn = page.locator('button[data-item-id="hours"]')
                if hours_btn.count():
                    hours_btn.click()
                    business.hours = extract_hours(page.locator('.t39EBf').inner_text())
            except: pass

            try:
                # Ratings and reviews
                rating_text = page.locator('div.F7nice >> span[aria-label]').first.get_attribute('aria-label')
                if rating_text:
                    business.rating = float(re.search(r"(\d+\.\d+)", rating_text).group(1))
                    business.reviews = int(re.search(r"(\d+) reviews", rating_text).group(1).replace(',', ''))
            except: pass

            try:
                # Business category
                business.category = page.locator('button[data-item-id="category"]').inner_text()
            except: pass

            business_list.business_list.append(business)
            page.wait_for_timeout(1000)

        business_list.save_to_excel('google_maps_data')
        business_list.save_to_csv('google_maps_data')

        context.close()
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-l", "--location", type=str)
    args = parser.parse_args()
    search_for = f"{args.search} {args.location}" if args.location and args.search else "ecommerce California"
    main(search_for)