import pandas as pd
from pybaseball import playerid_lookup, statcast_batter, statcast_pitcher
import os
import time
import warnings
warnings.filterwarnings('ignore')

from pybaseball import cache
cache.enable()

print("Pulling 2024 Brewers Statcast Data")
print("=" * 50)

# ─────────────────────────────────────────
# Brewers key batters 2024
# ─────────────────────────────────────────
BREWERS_BATTERS = [
    ('chourio', 'jackson'),
    ('contreras', 'william'),
    ('adames', 'willy'),
    ('mitchell', 'garrett'),
    ('wiemer', 'joey'),
    ('bauers', 'jake'),
    ('rhys', 'hoskins'),
    ('taylor', 'tyrone'),
    ('frelick', 'sal'),
    ('ortiz', 'oliver'),
]

BREWERS_PITCHERS = [
    ('peralta', 'freddy'),
    ('cobb', 'alex'),
    ('black', 'mason'),
    ('quintana', 'jose'),
    ('ashby', 'aaron'),
    ('megill', 'trevor'),
    ('williams', 'devin'),
    ('abner', 'uribe'),
]

START_DATE = '2024-04-01'
END_DATE = '2024-09-29'

os.makedirs('data/batters', exist_ok=True)
os.makedirs('data/pitchers', exist_ok=True)

# ─────────────────────────────────────────
# Pull batter data
# ─────────────────────────────────────────
print("\nPulling batter Statcast data...")
batter_frames = []

for last, first in BREWERS_BATTERS:
    try:
        result = playerid_lookup(last, first)
        if len(result) == 0:
            print(f"  ⚠️  Not found: {first} {last}")
            continue
        
        player_id = int(result.sort_values(
            'mlb_played_last', ascending=False
        ).iloc[0]['key_mlbam'])
        
        print(f"  Pulling {first.title()} {last.title()}...")
        data = statcast_batter(START_DATE, END_DATE, player_id)
        
        if len(data) > 0:
            data['player_type'] = 'batter'
            batter_frames.append(data)
            filepath = f"data/batters/{first}_{last}.csv"
            data.to_csv(filepath, index=False)
            print(f"    ✅ {len(data)} rows saved")
        
        time.sleep(1)  # be nice to Baseball Savant
        
    except Exception as e:
        print(f"  ❌ Error for {first} {last}: {e}")

# ─────────────────────────────────────────
# Pull pitcher data
# ─────────────────────────────────────────
print("\nPulling pitcher Statcast data...")
pitcher_frames = []

for last, first in BREWERS_PITCHERS:
    try:
        result = playerid_lookup(last, first)
        if len(result) == 0:
            print(f"  ⚠️  Not found: {first} {last}")
            continue

        player_id = int(result.sort_values(
            'mlb_played_last', ascending=False
        ).iloc[0]['key_mlbam'])

        print(f"  Pulling {first.title()} {last.title()}...")
        data = statcast_pitcher(START_DATE, END_DATE, player_id)

        if len(data) > 0:
            data['player_type'] = 'pitcher'
            pitcher_frames.append(data)
            filepath = f"data/pitchers/{first}_{last}.csv"
            data.to_csv(filepath, index=False)
            print(f"    ✅ {len(data)} rows saved")

        time.sleep(1)

    except Exception as e:
        print(f"  ❌ Error for {first} {last}: {e}")

# ─────────────────────────────────────────
# Combine and summarize
# ─────────────────────────────────────────
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)

if batter_frames:
    all_batters = pd.concat(batter_frames, ignore_index=True)
    all_batters.to_csv('data/all_brewers_batters.csv', index=False)
    print(f"Total batter rows:   {len(all_batters):,}")
    print(f"Unique batters:      {all_batters['player_name'].nunique()}")
    print(f"Date range:          {all_batters['game_date'].min()} to {all_batters['game_date'].max()}")

if pitcher_frames:
    all_pitchers = pd.concat(pitcher_frames, ignore_index=True)
    all_pitchers.to_csv('data/all_brewers_pitchers.csv', index=False)
    print(f"Total pitcher rows:  {len(all_pitchers):,}")
    print(f"Unique pitchers:     {all_pitchers['player_name'].nunique()}")

print("\nAll data saved to data/ folder!")
print("Ready to build the warehouse and dashboard.")