#!/usr/bin/env python3
def extract_cities(file_path):
    cities_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        current_var = None
        collecting = False
        city_lines = []
        
        for line in file:
            stripped_line = line.strip()
            
            # Check if the line starts a new city list
            if not collecting and ' = [' in stripped_line:
                current_var = stripped_line.split(' = [')[0].strip()
                collecting = True
                city_lines = []
            elif collecting:
                # Check if the line ends the current list
                if ']' in stripped_line:
                    collecting = False
                    # Process collected lines
                    cities_str = ' '.join(city_lines) + ' ' + stripped_line.replace(']', '')
                    cities = [c.strip(' "\'') for c in cities_str.split(',') if c.strip()]
                    cities_dict[current_var] = cities
                    current_var = None
                else:
                    city_lines.append(stripped_line)
    
    return cities_dict

if __name__ == "__main__":
    file_path = 'Classification.txt'
    cities = extract_cities(file_path)
    print(type(cities))
    for key, value in cities.items():
        print(key, value)