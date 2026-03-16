"""
Fetch Swiss occupation data from Eurostat (employment) and BFS PXWEB API (wages).
"""
import requests
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_eurostat_employment():
    """Fetch employment by ISCO-08 2-digit for Switzerland from Eurostat."""
    print("Fetching Eurostat employment data...")
    url = (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egai2d"
        "?geo=CH&time=2023&sex=T&age=Y15-64"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()

    isco_labels = data["dimension"]["isco08"]["category"]["label"]
    isco_index = data["dimension"]["isco08"]["category"]["index"]
    values = data.get("value", {})

    occupations = []
    for code, label in sorted(isco_labels.items(), key=lambda x: isco_index[x[0]]):
        idx = isco_index[code]
        val = values.get(str(idx))
        if val is not None and code not in ("TOTAL", "NRP"):
            # Determine if this is a major group (1-digit) or sub-group (2-digit)
            is_major = len(code) <= 3  # OC1..OC9, OC0
            isco_num = code.replace("OC", "")
            occupations.append({
                "isco_code": isco_num,
                "title_en": label,
                "employment_thousands": val,
                "employment": round(val * 1000),
                "is_major_group": is_major,
            })

    out_path = os.path.join(DATA_DIR, "eurostat_employment.json")
    with open(out_path, "w") as f:
        json.dump(occupations, f, indent=2)
    print(f"  Saved {len(occupations)} occupations to {out_path}")
    return occupations


def fetch_bfs_wages():
    """Fetch median wages by ISCO-08 occupation group from BFS PXWEB API."""
    print("Fetching BFS wage data...")
    base = "https://www.pxweb.bfs.admin.ch/api/v1/de"
    table = "px-x-0304010000_205"
    url = f"{base}/{table}/{table}.px"

    # Get metadata for occupation group codes
    meta_r = requests.get(url, timeout=15)
    meta_r.raise_for_status()
    meta = meta_r.json()

    occ_var = next(v for v in meta["variables"] if v["text"] == "Berufsgruppe")
    all_codes = occ_var["values"]
    code_to_name = dict(zip(occ_var["values"], occ_var["valueTexts"]))

    # Query: Switzerland, all occupations, total age, total gender, median (Zentralwert)
    query = {
        "query": [
            {"code": "Jahr", "selection": {"filter": "item", "values": ["2022"]}},
            {"code": "Grossregion", "selection": {"filter": "item", "values": ["-1"]}},
            {"code": "Berufsgruppe", "selection": {"filter": "item", "values": all_codes}},
            {"code": "Lebensalter", "selection": {"filter": "item", "values": ["-1"]}},
            {"code": "Geschlecht", "selection": {"filter": "item", "values": ["-1"]}},
            {"code": "Zentralwert und andere Perzentile", "selection": {"filter": "item", "values": ["1"]}},
        ],
        "response": {"format": "json"},
    }

    r = requests.post(url, json=query, timeout=30)
    r.raise_for_status()
    data = r.json()

    # ISCO code mapping: BFS uses codes like "10", "11", "21" etc.
    wages = {}
    for entry in data.get("data", []):
        occ_code = entry["key"][2]  # Berufsgruppe code
        val = entry["values"][0]
        name_de = code_to_name.get(occ_code, "")
        if val and val != ".." and occ_code != "-1":
            # Clean the name: remove "> " prefix
            name_de = name_de.lstrip("> ").strip()
            wages[occ_code] = {
                "isco_code": occ_code,
                "title_de": name_de,
                "median_wage_monthly_chf": int(val),
                "median_wage_annual_chf": int(val) * 12,
            }

    out_path = os.path.join(DATA_DIR, "bfs_wages.json")
    with open(out_path, "w") as f:
        json.dump(wages, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(wages)} wage entries to {out_path}")
    return wages


if __name__ == "__main__":
    employment = fetch_eurostat_employment()
    wages = fetch_bfs_wages()
    print(f"\nDone! {len(employment)} occupations, {len(wages)} wage entries.")
