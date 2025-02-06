#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Configure browser with better stealth
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    
    # Create context with language preferences
    context = browser.new_context(
        locale="en-US",
        permissions=["geolocation"]
    )
    page = context.new_page()
    
    # Navigate to Google
    page.goto("https://www.google.com")
    
    try:
        # Handle cookie consent (specific to Google's dialog)
        page.wait_for_selector('button:has-text("Accept all")', timeout=5000)
        page.click('button:has-text("Accept all")')
        print("Accepted cookies successfully!")
    except:
        print("No cookie consent dialog found or already accepted")
    
    # Handle search directly (no language selection needed)
    try:
        # Wait for search box to be ready
        page.wait_for_selector('textarea[name="q"]', timeout=5000)
        print("Google search page loaded successfully!")
        
        # Example search interaction
        page.fill('textarea[name="q"]', 'test search')
        page.keyboard.press('Enter')
        
        # Wait for results
        page.wait_for_selector('#search', timeout=10000)
        page.screenshot(path="google_search_results.png")
        
    except Exception as e:
        print(f"Error during search interaction: {str(e)}")
    
    browser.close()