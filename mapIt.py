#!/usr/bin/env python3


import webbrowser, sys, pyperclip

if len(sys.argv) > 1:
    address = sys.argv[1:]
    address = ' '.join(address)
    print(address)
else:
    address = pyperclip.paste()

webbrowser.open('www.google.com/maps/place/' + address)
