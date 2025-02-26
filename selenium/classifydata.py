#!/usr/bin/env python3

import pandas as pd


extract_cities = __import__("extractfromtxt").extract_cities
cities_by_country = extract_cities("Classification.txt")
filePath = "resultsALL.xlsx"
mapping = {}
for country, cities in cities_by_country.items():
    for city in cities:
        mapping[city] = country

# print(mapping)



dataframe = pd.read_excel(filePath)
dataframe['Country'] = dataframe['City'].map(mapping).fillna('Unkown')

with pd.ExcelWriter('UpdatedAll.xlsx') as writer:
    for country in dataframe['Country'].unique():
        df_country = dataframe[dataframe["Country"] == country]
        df_country.to_excel(writer, sheet_name=country, index=False)
