import pandas as pd
from pybaseball import playerid_lookup, statcast_batter, statcast_pitcher
import os
import warnings
warnings.filterwarnings('ignore')

from pybaseball import cache
cache.enable()

START_DATE = '2024-04-01'
END_DATE = '2024-09-29'

print("Fixing missing players...")

# ─────────────────────────────────────────
# Try different name variations
# ─────────────────────────────────────────

# Rhys Hoskins
print("\nLooking up Rhys Hoskins...")
result = playerid_lookup('hoskins', 'rhys')
print(result[['name_first', 'name_last', 'key_mlbam', 'mlb_played_first', 'mlb_played_last']])

# Christian Yelich
print("\nLooking up Christian Yelich...")
result = playerid_lookup('yelich', 'christian')
print(result[['name_first', 'name_last', 'key_mlbam', 'mlb_played_first', 'mlb_played_last']])

# Abner Uribe
print("\nLooking up Abner Uribe...")
result = playerid_lookup('uribe', 'abner')
print(result[['name_first', 'name_last', 'key_mlbam', 'mlb_played_first', 'mlb_played_last']])

# Joey Wiemer — check if ID is right
print("\nLooking up Joey Wiemer...")
result = playerid_lookup('wiemer', 'joey')
print(result[['name_first', 'name_last', 'key_mlbam', 'mlb_played_first', 'mlb_played_last']])