#!/usr/bin/env python3

import pandas as pd
from playwright.sync_api import sync_playwright
print(pd.__version__)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://google.com')
    page.screenshot(path='example.png')
    browser.close()

print('playwright is working fine check example.png in the directory')