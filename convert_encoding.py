import json
import codecs

# Read the file with UTF-16 encoding
with codecs.open('temp_foods.json', 'r', encoding='utf-16') as f:
    data = json.load(f)

# Write with UTF-8 (no BOM)
with open('foods_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("✅ Converted to UTF-8 without BOM")