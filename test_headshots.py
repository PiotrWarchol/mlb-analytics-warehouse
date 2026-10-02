import urllib.request
from player_ids import BATTER_IDS, get_headshot_url

print("Testing headshot URLs...")

for name, player_id in list(BATTER_IDS.items())[:3]:
    url = get_headshot_url(player_id)
    try:
        req = urllib.request.urlopen(url, timeout=5)
        print(f"  ✅ {name} — {req.status} — {url}")
    except Exception as e:
        print(f"  ❌ {name} — {e}")