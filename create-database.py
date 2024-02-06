import random
import sqlite3

import numpy as np

from constants import *


def init():
  print("Initializing...")

  global already_stored_ingredients
  global recipies_to_scrape
  global progress_checkpoints

  print(" Initializing database...")
  init_db()
  print(" Database ready!")
  already_stored_ingredients = []
  print("Initializing done!\nStarting...")

  recipies_to_scrape = int(input("\nHow many recipies do you want?\n"))

  progress_checkpoints = np.linspace(recipies_to_scrape / 20, recipies_to_scrape, 20).astype(int).tolist()


def init_db():
  global connection
  global cursor

  print("   Connecting to database...")
  connection = sqlite3.connect('database.db')
  cursor = connection.cursor()
  print("   Connection established!")

  print("   Dropping tables if there are any...")
  cursor.execute("DROP TABLE IF EXISTS ingredient")
  cursor.execute("DROP TABLE IF EXISTS recipe_ingredient")
  cursor.execute("DROP TABLE IF EXISTS recipe")
  print("   Tables dropped!")

  print("   Creating new tables...")
  cursor.execute(
    'CREATE TABLE ingredient (name VARCHAR(255) PRIMARY KEY, unit VARCHAR(255))')
  cursor.execute(
    'CREATE TABLE recipe (id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL, instructions VARCHAR(255))')
  cursor.execute(
    'CREATE TABLE recipe_ingredient (id INTEGER NOT NULL PRIMARY KEY, amount DOUBLE, parent_recipe INTEGER NOT NULL, parent_ingredient INTEGER NOT NULL, FOREIGN KEY(parent_recipe) REFERENCES recipe(id), FOREIGN KEY(parent_ingredient) REFERENCES ingredient(name))')
  print("   Tables created!")


def add_recipe(recipe):
  cursor.execute("INSERT INTO recipe (id, name, instructions) VALUES (?, ?, ?)",
                 ((recipe['id'], recipe['title'], ' '.join(recipe['directions']))))


def extract_unit(recipe, ingredient_index):
  for unit in UNITS:
    if type(unit) is tuple:
      unit = unit[0]
    if unit in recipe["ingredients"][ingredient_index].lower():
      return unit.strip()


def add_ingredient(recipe, ingredient, ingredient_index):
  unit = extract_unit(recipe, ingredient_index)

  cursor.execute("INSERT OR IGNORE INTO ingredient (name, unit) VALUES (?, ?)",
                 (ingredient, unit))


def recipe_follows_previous_units_standards(recipe):
  for index, ingredient in enumerate(recipe['NER']):
    previously_set_unit = cursor.execute("SELECT unit FROM ingredient WHERE name = ?", (ingredient,)).fetchone()

    if previously_set_unit is None:
      continue
    else:
      if previously_set_unit[0] is not None:
        if previously_set_unit[0] not in recipe['ingredients'][index]:
          return False
      else:
        for unit in UNITS:
          if unit[0] in recipe['ingredients'][index].lower():
            return False

  return True


def add_ingredients_and_recipe_ingredients(recipe):
  for ingredient_index, ingredient in enumerate(recipe["NER"]):
    add_ingredient(recipe, ingredient, ingredient_index)
    add_recipe_ingredient(recipe, ingredient_index)


def get_amount(detailed_ingredient):
  amount_unclean = detailed_ingredient[0:4]

  amount_clean = None

  try:
    if WHOLE_NUMBER_WITH_FRACTION.search(amount_unclean):
      amount_clean = int(amount_unclean[0]) + (float(amount_unclean[2] / float(amount_unclean[4])))
    elif FRACTION.search(amount_unclean):
      amount_clean = float(amount_unclean[0]) / float(amount_unclean[2])
    elif WHOLE_NUMBER.search(amount_unclean):
      amount_clean = int(amount_unclean[0])
    else:
      print(f"No amount found in '{amount_unclean}'")
      give_status_update(True)
  except:
    print(f"Error parsing '{amount_unclean}' to float")
    give_status_update(True)

  if amount_clean is not None:
    amount_clean = round(amount_clean, 2)

  return amount_clean


def add_recipe_ingredient(recipe, ingredient_index):
  detailed_ingredient = recipe["ingredients"][ingredient_index]
  ingredient_name = recipe["NER"][ingredient_index]

  amount = get_amount(detailed_ingredient)

  cursor.execute("INSERT INTO recipe_ingredient (amount, parent_recipe, parent_ingredient) VALUES (?, ?, ?)",
                 (amount, recipe['id'], ingredient_name))


def give_status_update(skip_throttler=False):
  global progress
  global progress_percentage
  global recipies_to_scrape
  global print_throttler

  progress_percentage = round(progress * 100 / recipies_to_scrape)

  if progress % print_throttler == 0 or skip_throttler:
    print(f"{progress}/{recipies_to_scrape} - {progress_percentage}%", end='\r')


def convert_temperatures():
  recipies = cursor.execute("SELECT id, instructions FROM recipe").fetchall()

  for instruction in recipies:
    span = TEMPERATURE_REGEX.search(instruction[1])

    if span is not None:
      fdegrees = int(instruction[1][span.start():span.end() - 1])
      cdegrees = str(round(round((fdegrees - 32) * (5 / 9)) / 10) * 10)

      new_instruction = instruction[1].replace(str(fdegrees), cdegrees).replace('°', '°C')

      cursor.execute("UPDATE recipe SET instructions = ? WHERE id = ?",
                     (new_instruction, instruction[0]))

      connection.commit()


def convert_units():
  for unit in UNITS:
    if type(unit) is tuple:
      old_unit = unit[0].strip()
      new_unit = unit[2]
      parent_ingredients_to_update = cursor.execute('SELECT name FROM ingredient WHERE unit = ?',
                                                    (old_unit,)).fetchall()

      cursor.execute('UPDATE ingredient SET unit = ? WHERE unit = ?', (new_unit, old_unit))

      for ingredient in parent_ingredients_to_update:
        cursor.execute(f'UPDATE recipe_ingredient SET amount = ROUND(amount*?, 1) WHERE parent_ingredient = ?',
                       (unit[1], ingredient[0]))

  connection.commit()


def convert_db_to_metric():
  convert_temperatures()
  convert_units()


def start():
  print("Starting...")
  print('Scraping dataset...')
  print("0%", end='\r')

  global progress

  with open('dataset/recipe_dataset.json') as json_file:
    for line in json_file:
      if progress >= recipies_to_scrape:
        connection.commit()
        break

      recipe = eval(line)

      # Skip header
      if recipe['id'] == '':
        continue

      if not recipe_follows_previous_units_standards(recipe):
        connection.rollback()
        continue

      add_recipe(recipe)
      add_ingredients_and_recipe_ingredients(recipe)

      connection.commit()

      give_status_update()

      progress += 1

  print("Converting units...")
  convert_db_to_metric()


def displayRecipe(random_recipe_id):
  recipe = cursor.execute(f'SELECT * FROM recipe WHERE id = ?', (random_recipe_id,)).fetchone()

  name = recipe[1]
  instructions = recipe[2].split('. ')
  instructions[-1] = instructions[-1][:-1]

  print(f"\n\nRandom Recipe ID: {random_recipe_id}")
  print('Random Recipe name: ', name)
  print('\nInstructions:')
  for n, instruction in enumerate(instructions, 1):
    print(f'{n}. {instruction}.')

  ingredient = cursor.execute(
    'SELECT recipe_ingredient.amount, recipe_ingredient.parent_ingredient, ingredient.unit FROM recipe_ingredient INNER JOIN ingredient ON recipe_ingredient.parent_ingredient = ingredient.name WHERE recipe_ingredient.parent_recipe = ?',
    (random_recipe_id,))

  print('\nIngredients: ')
  for row in ingredient:

    amount = row[0]
    ingredient = row[1]
    unit = row[2]

    if amount.is_integer():
      amount = int(amount)

    if unit == None:
      if amount == None:
        print(f'{ingredient}')
      print(f'{amount} {ingredient}')
    else:
      print(f'{amount} {unit} {ingredient}')


progress = 0
progress_percentage = 0
recipies_to_scrape = 0
print_throttler = 100

init()
start()

random_recipe_ids = cursor.execute("SELECT id FROM recipe").fetchall()
random_recipe_id = random_recipe_ids[random.randint(0, len(random_recipe_ids))][0]

displayRecipe(random_recipe_id)
