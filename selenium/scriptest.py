#!/usr/bin/python3

import sys

try:
    keyword_var = " ".join(sys.argv[1:])
except IndexError:
    keyword_var = 'ecommerce'

print("Keyword Variable:", keyword_var)
print("Script is continuing...")

# Simulating the rest of your script
for i in range(3):
    print(f"Processing step {i+1}...")
