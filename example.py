#!/usr/bin/env python3

import bs4, requests

with open('example.com', 'r', encoding='utf-8') as file:
    exampleSoup = bs4.BeautifulSoup(file.read(), 'html.parser')
print(exampleSoup.select('#author'))

pElem = exampleSoup.select('p')
print('P elements {}'.format(pElem[0].getText()))

spanElem = exampleSoup.select('span')
print('Span Elements {}'.format(spanElem[0].get('id')))


