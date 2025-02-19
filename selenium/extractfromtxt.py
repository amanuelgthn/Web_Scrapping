#!/usr/bin/env python3

countries = []

with open("Classification.txt") as file:
    for line in file:
        if line != "\n":
            countries.append(line)

count = 0
for items in countries:
    print(count, items)
    print("\n")
    count += 1
print(countries)