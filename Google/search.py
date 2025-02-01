#!/usr/bin/env python3

from collections import defaultdict
from http import client

from cssselect import Selector


def parse_search_results(selector: Selector):
    """parse search results from google search page"""
    results = []
    for box in selector.xpath("//h1[contains(text(),'Search Results')]/following-sibling::div[1]/div"):
        title = box.xpath(".//h3/text()").get()
        url = box.xpath(".//h3/../@href").get()
        text = "".join(box.xpath(".//div[@data-sncf]//text()").getall())
        if not title or not url:
            continue
        url = url.split("://")[1].replace("www.", "")
        results.append(title, url, text)
    return results


def scrape_search(query: str, page=1):
    """scrape search results for a given keyword"""
    # retrieve the SERP
    url = f"https://www.google.com/search?hl=en&q={quote(query)}" + (f"&start={10*(page-1)}" if page > 1 else "")
    print(f"scraping {query=} {page=}")
    results = defaultdict(list)
    response = client.get(url)
    assert response.status_code == 200, f"failed status_code={response.status_code}"
    # parse SERP for search result data
    selector = Selector(response.text)
    results["search"].extend(parse_search_results(selector))
    return dict(results)

# example use: scrape 3 pages: 1,2,3
for page in [1, 2, 3]:
    results = scrape_search("scrapfly blog", page=page)
    for result in results["search"]:
        print(result)