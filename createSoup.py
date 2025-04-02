#!/usr/bin/env python3

import requests, bs4
import urllib3

http = urllib3.PoolManager()


response = requests.get('http://nostarch.com')
response.raise_for_status()
noStarchSoup = bs4.BeautifulSoup(response.text)
print(type(noStarchSoup))
r = http.request('GET', 'http://nostarch.com')

soup = bs4.BeautifulSoup(r.data, 'lxml')
print(noStarchSoup)

print('soup method {}'.format(soup.title))
print('soup title text {}'.format(soup.title.text))