# MLB player IDs for our Brewers roster
# These come from our pybaseball playerid_lookup results

BATTER_IDS = {
    'Jackson Chourio': 694192,
    'William Contreras': 661388,
    'Willy Adames': 642715,
    'Garrett Mitchell': 669003,
    'Joey Wiemer': 686894,
    'Jake Bauers': 641343,
    'Rhys Hoskins': 656555,
    'Tyrone Taylor': 621438,
    'Sal Frelick': 686217,
    'Christian Yelich': 592885,
}

PITCHER_IDS = {
    'Freddy Peralta': 642547,
    'Alex Cobb': 502054,
    'Mason Black': 694004,
    'Jose Quintana': 500779,
    'Aaron Ashby': 671308,
    'Trevor Megill': 669330,
    'Devin Williams': 634669,
    'Abner Uribe': 682842,
}

def get_headshot_url(player_id):
    """Get MLB headshot URL for a player ID."""
    return (
        f"https://img.mlbstatic.com/mlb-photos/image/upload/"
        f"d_people:generic:headshot:67:current.png/"
        f"w_213,q_auto:best/v1/people/{player_id}/"
        f"headshot/67/current"
    )

def get_player_id(name, batter_ids=BATTER_IDS, pitcher_ids=PITCHER_IDS):
    """Get MLB ID for a player by name."""
    if name in batter_ids:
        return batter_ids[name]
    if name in pitcher_ids:
        return pitcher_ids[name]
    return None