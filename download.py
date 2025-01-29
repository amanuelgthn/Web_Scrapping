#!/usr/bin/env python3


import requests
url = 'https://example.com/sample.txt'
response = requests.get(url)
if response.status_code:
    with open('Automate_the_Boring_Stuff_with_Python.epub', 'wb') as f:
        f.write(response.content)
        print('downloaded')
else:
    print

print(len(response.text))
print(response.text)