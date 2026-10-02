import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher
import os
import time
import warnings
warnings.filterwarnings('ignore')

from pybaseball import cache
cache.enable()

START_DATE = '2024-04-01'
END_DATE = '2024-09-29'

os.makedirs('data/batters', exist_ok=True)
os.makedirs('data/pitchers', exist_ok=True)

# IDs from our lookup
MISSING_BATTERS = [
    ('Rhys Hoskins', 656555),
    ('Christian Yelich', 592885),
]

MISSING_PITCHERS = [
    ('Abner Uribe', 682842),
]

print("Pulling missing player data...")

# Batters
print("\nBatters:")
batter_frames = []
for name, player_id in MISSING_BATTERS:
    print(f"  Pulling {name}...")
    data = statcast_batter(START_DATE, END_DATE, player_id)
    if len(data) > 0:
        filename = name.lower().replace(' ', '_')
        data.to_csv(f'data/batters/{filename}.csv', index=False)
        batter_frames.append(data)
        print(f"    ✅ {len(data)} rows saved")
    time.sleep(1)

# Pitchers
print("\nPitchers:")
pitcher_frames = []
for name, player_id in MISSING_PITCHERS:
    print(f"  Pulling {name}...")
    data = statcast_pitcher(START_DATE, END_DATE, player_id)
    if len(data) > 0:
        filename = name.lower().replace(' ', '_')
        data.to_csv(f'data/pitchers/{filename}.csv', index=False)
        pitcher_frames.append(data)
        print(f"    ✅ {len(data)} rows saved")
    time.sleep(1)

# ─────────────────────────────────────────
# Rebuild combined files
# ─────────────────────────────────────────
print("\nRebuilding combined datasets...")

# Load all batter CSVs
all_batter_files = [f for f in os.listdir('data/batters') if f.endswith('.csv')]
all_batters = pd.concat([
    pd.read_csv(f'data/batters/{f}') for f in all_batter_files
], ignore_index=True)
all_batters.to_csv('data/all_brewers_batters.csv', index=False)

# Load all pitcher CSVs
all_pitcher_files = [f for f in os.listdir('data/pitchers') if f.endswith('.csv')]
all_pitchers = pd.concat([
    pd.read_csv(f'data/pitchers/{f}') for f in all_pitcher_files
], ignore_index=True)
all_pitchers.to_csv('data/all_brewers_pitchers.csv', index=False)

print("\n" + "=" * 50)
print("UPDATED SUMMARY")
print("=" * 50)
print(f"Total batter rows:   {len(all_batters):,}")
print(f"Unique batters:      {all_batters['player_name'].nunique()}")
print(f"Batters:             {sorted(all_batters['player_name'].unique())}")
print(f"\nTotal pitcher rows:  {len(all_pitchers):,}")
print(f"Unique pitchers:     {all_pitchers['player_name'].nunique()}")
print(f"Pitchers:            {sorted(all_pitchers['player_name'].unique())}")
print("\nAll data updated!")