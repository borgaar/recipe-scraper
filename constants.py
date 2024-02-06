import re

UNITS = [
  ' tsp.', ' tbsp.', ' pkg.', (' cup', 2.366, 'dl'), (' pint', 0.568, "liter"), (' quart', 0.946, 'l'),
  (' gallon', 3.785, 'liter'), (' oz', 28.35, 'g'), (' lb', 0.454, 'kg'), ' mg', ' g ', ' kg', ' ml', 'pinch',
  ' dash', ' clove', ' can', ' jar', ' package', ' box', ' bunch', ' stalk', ' slice', ' piece', ' head', ' bag',
  ' bunch', ' bottle', ' carton', ' container', ' jar', ' package', ' packet', (' pound', 0.454, 'kg'),
  (' c.', 2.366, 'dl'), ' clump', (' gal.', 3.785, 'liter')]

WHOLE_NUMBER_WITH_FRACTION = re.compile(r'\d \d/\d')
FRACTION = re.compile(r'\d/\d')
WHOLE_NUMBER = re.compile(r'\d')

TEMPERATURE_REGEX = re.compile(r'\d+°')
