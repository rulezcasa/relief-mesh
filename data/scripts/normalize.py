"""Normalize the raw Overpass export into the offline gazetteer.

Input:  data/raw/raw_places.json     (Overpass `out center tags` JSON)
Output: data/normalized/places.json  ([{id, name, lat, lon, kind}, ...])

Run once during setup:  python3 data/scripts/normalize_places.py
"""
import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = DATA_DIR / "raw" / "raw_places.json"
OUT_PATH = DATA_DIR / "normalized" / "places.json"

# Tag keys checked in order to label what a place is, e.g. amenity=pharmacy -> "pharmacy".
KIND_KEYS = ["amenity", "shop", "healthcare", "public_transport", "railway", "highway",
             "leisure", "tourism", "historic", "office", "building", "landuse", "place", "man_made"]

# Kinds that say little about a place; a duplicate with a more specific kind replaces them.
GENERIC_KINDS = {"other", "building", "transit_stop"}


def coords(el):
    if "lat" in el:
        return el["lat"], el["lon"]
    center = el.get("center")
    return (center["lat"], center["lon"]) if center else (None, None)


def kind_of(tags):
    for key in KIND_KEYS:
        if key not in tags:
            continue
        if key == "public_transport":
            return "transit_stop"      # stop_position / platform / stop_area are one stop to a person
        value = tags[key]
        return key if value == "yes" else value    # building=yes -> "building"
    return "other"


def main():
    elements = json.load(open(RAW_PATH))["elements"]

    places = {}                    # (name, ~100m grid cell) -> place; collapses near-duplicates
    streets = defaultdict(list)    # street name -> segment centres, merged into one point below

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        lat, lon = coords(el)
        if not name or lat is None or tags.get("type") == "route":
            continue

        if "highway" in tags and el["type"] == "way":
            streets[name].append((lat, lon))
            continue

        kind = kind_of(tags)
        key = (name.lower(), round(lat, 3), round(lon, 3))
        existing = places.get(key)
        if existing is None or (existing["kind"] in GENERIC_KINDS and kind not in GENERIC_KINDS):
            places[key] = {"name": name, "lat": round(lat, 6), "lon": round(lon, 6), "kind": kind}

    for name, pts in streets.items():
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        places[(name.lower(), "street")] = {"name": name, "lat": round(lat, 6),
                                            "lon": round(lon, 6), "kind": "street"}

    rows = sorted(places.values(), key=lambda p: (p["name"].lower(), p["kind"]))
    out = [{"id": f"p{i:04d}", **p} for i, p in enumerate(rows, start=1)]

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    kinds = defaultdict(int)
    for p in out:
        kinds[p["kind"]] += 1
    top = sorted(kinds.items(), key=lambda kv: -kv[1])[:10]
    print(f"{len(elements)} raw elements -> {len(out)} places ({len(streets)} streets)")
    print("top kinds:", ", ".join(f"{k} {n}" for k, n in top))


if __name__ == "__main__":
    main()
