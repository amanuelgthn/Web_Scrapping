#!/usr/bin/env python3

import requests, bs4

response = requests.get('http://nostarch.com')
response.raise_for_status()
noStarchSoup = bs4.BeautifulSoup(response.text)
print(type(noStarchSoup))

print(noStarchSoup)