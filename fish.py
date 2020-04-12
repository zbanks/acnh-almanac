import pprint
import json

# Note: This script is largely based on educated guesses, not from analysis
# or decompilation of the game's executable, except when noted otherwise

HEMISPHERES = ["North", "South"]
SIZES = ["SS", "S", "M", "L", "LL", "LLL", "U", "J", "K"]
SIZE_GROUPS = {
    # Overlapping groups: assume it's hard to differentiate adjacent sizes
    # This is subjective
    "Small": ["SS", "S", "M"],
    "Medium": ["S", "M", "L", "LL"],
    "Large": ["L", "LL", "LLL"],
    "Special": ["U", "J", "K"],  # Eels & Fins
}
SIZE_REV = {
    # Subjective "inverse" of SIZE_GROUPS
    "SS": "Small",
    "S": "Small",
    "M": "Medium",
    "L": "Medium",
    "LL": "Large",
    "LLL": "Large",
    "U": "Special",
    "J": "Special",
    "K": "Special",
}
LOCATIONS = ["River", "RiverCliffTop", "Pond", "BrackishWater", "Sea", "Anywhere", "SeaBeachBridge"]
LOCATION_GROUPS = {
    # In a given spot, what other categories of fish could also be there?
    # This is vaugely a guess
    "River": ("River", ["River", "Anywhere"]),
    "Clifftop": ("River", ["River", "RiverCliffTop", "Anywhere"]),
    "Pond": ("River", ["Pond", "Anywhere"]),
    "River Mouth": ("River", ["River", "BrackishWater", "Anywhere"]),
    "Sea": ("Sea", ["Sea", "Anywhere"]),
    "Dock": ("Sea", ["Sea", "Anywhere", "SeaBeachBridge"]),
}
TIMES = {
    # No fish in the database is _only_ available during "mid"; or "morning" and "night" but not "mid"
    "mid": [1, 3], # 9pm - 4am & 9am - 4pm
    "morning": [2], # 4am - 9am; known as "0816" in Treeki's analysis
    "night": [4], # 4pm - 9pm; known as "1923" in Treeki's analysis
}
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()

def load_fish_data():
    with open("data/FishStatusParam.json") as f:
        fish_status = json.load(f)
    with open("data/FishAppearRiverParam.json") as f:
        fish_appear_river = json.load(f)
    with open("data/FishAppearSeaParam.json") as f:
        fish_appear_sea = json.load(f)
    with open("data/item_prices.json") as f:
        item_prices = json.load(f)

    data = {}
    for fish in fish_status:
        fish_id = fish["fish_id"]
        data[fish_id] = f = {
            "id": fish["fish_id"],
            "size": fish["fish_size"],
            "location": fish["_0de2a3be"],
            "rain_penalty?": fish["_eac6a012"], # this is a total guess
            "price": item_prices[fish_id],
            "appear": {},
        }
        assert f["size"] in SIZES
        assert f["location"] in LOCATIONS

    for area, rows in [("River", fish_appear_river), ("Sea", fish_appear_sea)]:
        for row in rows:
            hemisphere = HEMISPHERES[row["hemisphere"]]
            fish = data[row["fish_id"]]
            for month in MONTHS:
                for time in TIMES:
                    fish["appear"][(hemisphere, area, month, time)] = row[month + "_" + time]
    return data

# This would probably work much better as a pandas dataframe or something
FISH_DATA = load_fish_data()

def whats_here(hemisphere, area, month, time, raining=False, size=None):
    assert hemisphere in HEMISPHERES
    assert area in LOCATION_GROUPS
    assert month in MONTHS
    assert time in TIMES

    # There's some built-in assumptions here about how fish are spawned:
    # we're assuming the game is trying to spawn a fish in a particular
    # sub-reigion (e.g. Clifftop) -- but maybe the game instead just
    # tries to spawn a fish, and *then* after selecting the fish it 
    # decides where to put it? Or maybe the regions are weighted?
    gross_area, locations = LOCATION_GROUPS[area]

    available = {}
    total_p = 0
    total_bells = 0
    for name, fish in FISH_DATA.items():
        if fish["location"] not in locations:
            continue
        if size is not None and fish["size"] not in SIZE_GROUPS[size]:
            continue
        p = fish["appear"].get((hemisphere, gross_area, month, time), 0)
        if not raining:
            # This is a complete guess at how rain factors in
            p *= 1.0 - fish["rain_penalty?"] / 100.
        if p > 0:
            available[name] = p
            total_p += p
            total_bells += p * fish["price"]
    if total_p == 0:
        return 0, {}

    for k, v in available.items():
        available[k] = v / total_p
    ev = total_bells / total_p
    return ev, available

def how_to_catch(hemisphere, month, fishes):
    assert hemisphere in HEMISPHERES
    assert month in MONTHS
    assert all(f in FISH_DATA for f in fishes)

    results = {}
    for area, (gross_area, locations) in LOCATION_GROUPS.items():
        for time in TIMES:
            for raining in (False, True):
                _ev, probs = whats_here(hemisphere, area, month, time, raining=raining)
                prob_sum = sum([probs.get(f, 0) for f in fishes])
                if prob_sum > 0:
                    results[(area, time, raining)] = prob_sum
    return results

def print_sorted(d):
    pprint.pprint(sorted(d.items(), key=lambda x: -x[1]))

def main():
    print("What's available right now?")
    hemisphere = "North"
    month = "apr"
    time = "night"
    for location in sorted(LOCATION_GROUPS):
        ev, probs = whats_here(hemisphere, location, month, time)
        print(location, ev)
        print_sorted(probs)
    print()

    print("How to catch blue marlin & tuna:")
    print_sorted(how_to_catch(hemisphere, month, ["blue marlin", "tuna"]))
    print()

    print("Best times to fish for money:")
    location_ev = {}
    for hemisphere in HEMISPHERES:
        for location in sorted(LOCATION_GROUPS):
            for month in MONTHS:
                for time in TIMES:
                    for raining in (True, False):
                        ev, probs = whats_here(hemisphere, location, month, time, raining=raining)
                        location_ev[(hemisphere, location, month, time, raining)] = ev
    print_sorted(location_ev)
    print()

if __name__ == "__main__":
    main()
