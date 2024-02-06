import csv
import json

csv_file_path = 'dataset/full_dataset.csv'
json_file_path = 'dataset/recipe_dataset.json'

# Define the CSV columns based on your sample data
columns = ["id", "title", "ingredients", "directions", "link", "source", "NER"]

with open(csv_file_path, 'r', encoding='utf-8') as csv_file, \
    open(json_file_path, 'w', encoding='utf-8') as json_file:
  # Create a CSV reader
  reader = csv.reader(csv_file)

  print("Conversion started. This could take a few minutes...")

  for row_count, row in enumerate(reader):
    if row_count % 1000 == 0:
      print(f"{row_count}/~2.3 million rows completed", end='\r')

    # Skip empty rows
    if not row:
      continue

    # Create a dictionary for the JSON object
    data = {}
    for i, column in enumerate(columns):
      # Check if the column exists in the current row
      if i < len(row):
        # Attempt to interpret JSON-like strings as JSON objects
        try:
          data[column] = json.loads(row[i])
        except json.JSONDecodeError:
          data[column] = row[i]

    # Write the JSON object to the file
    json.dump(data, json_file)
    json_file.write("\n")

print("CSV to JSON conversion completed.")
