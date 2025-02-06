#!/usr/bin/env python3

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context("./my-profile", headless=False)
    page = context.new_page()
    page.goto("https://www.google.com/maps")

    input("Please Enter after manually accepting the cookie consent...")
    context.storage_state(path="cookies.json")
    context.close()