"""
Process and merge Swiss occupation data: Eurostat employment + BFS wages.
Produces occupations.json with all fields needed for the visualization.
"""
import json
import os
import csv

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ISCO-08 major group labels
MAJOR_GROUPS = {
    "0": "Armed Forces",
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and Associate Professionals",
    "4": "Clerical Support Workers",
    "5": "Service and Sales Workers",
    "6": "Skilled Agricultural, Forestry and Fishery Workers",
    "7": "Craft and Related Trades Workers",
    "8": "Plant and Machine Operators and Assemblers",
    "9": "Elementary Occupations",
}

# Education level typical for each ISCO major group
# Based on ISCO-08 skill levels
EDUCATION_BY_MAJOR = {
    "0": "Military training",
    "1": "Bachelor's degree or higher",
    "2": "Bachelor's degree or higher",
    "3": "Professional diploma / Higher vocational",
    "4": "Upper secondary / Vocational",
    "5": "Upper secondary / Vocational",
    "6": "Upper secondary / Vocational",
    "7": "Upper secondary / Vocational",
    "8": "Upper secondary or less",
    "9": "No formal education required",
}

# Education numeric level for coloring (1=lowest, 5=highest)
EDUCATION_LEVEL = {
    "No formal education required": 1,
    "Upper secondary or less": 2,
    "Upper secondary / Vocational": 3,
    "Professional diploma / Higher vocational": 4,
    "Bachelor's degree or higher": 5,
    "Military training": 3,
}


def load_employment():
    with open(os.path.join(DATA_DIR, "eurostat_employment.json")) as f:
        return json.load(f)


def load_wages():
    with open(os.path.join(DATA_DIR, "bfs_wages.json")) as f:
        return json.load(f)


def merge_data():
    employment = load_employment()
    wages = load_wages()

    # Build wage lookup by ISCO code
    wage_lookup = {w["isco_code"]: w for w in wages.values()}

    occupations = []
    for emp in employment:
        code = emp["isco_code"]
        # Skip major groups — only use 2-digit sub-groups
        if emp["is_major_group"]:
            continue
        # Skip armed forces sub-groups (very small, unreliable data)
        if code.startswith("0") and len(code) > 1:
            continue

        major = code[0]
        category = MAJOR_GROUPS.get(major, "Other")
        education = EDUCATION_BY_MAJOR.get(major, "Unknown")

        # Match wage data
        wage_info = wage_lookup.get(code, {})
        monthly_wage = wage_info.get("median_wage_monthly_chf")
        annual_wage = wage_info.get("median_wage_annual_chf")

        slug = emp["title_en"].lower()
        for ch in [",", "'", ".", "(", ")"]:
            slug = slug.replace(ch, "")
        slug = slug.replace(" ", "-").replace("--", "-").strip("-")

        occ = {
            "title": emp["title_en"],
            "slug": slug,
            "isco_code": code,
            "category": category,
            "jobs": emp["employment"],
            "pay_monthly": monthly_wage,
            "pay_annual": annual_wage,
            "education": education,
            "education_level": EDUCATION_LEVEL.get(education, 0),
        }
        occupations.append(occ)

    # Sort by category then employment
    occupations.sort(key=lambda x: (x["category"], -x["jobs"]))

    return occupations


def save_csv(occupations):
    out_path = os.path.join(os.path.dirname(__file__), "occupations.csv")
    fields = ["title", "slug", "isco_code", "category", "jobs", "pay_monthly",
              "pay_annual", "education", "education_level"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(occupations)
    print(f"Saved {len(occupations)} occupations to {out_path}")


def save_json(occupations):
    out_path = os.path.join(os.path.dirname(__file__), "occupations.json")
    with open(out_path, "w") as f:
        json.dump(occupations, f, indent=2)
    print(f"Saved {len(occupations)} occupations to {out_path}")


if __name__ == "__main__":
    occupations = merge_data()

    total_jobs = sum(o["jobs"] for o in occupations)
    with_wages = sum(1 for o in occupations if o["pay_monthly"])
    print(f"Merged: {len(occupations)} occupations, {total_jobs:,} total jobs, {with_wages} with wage data")

    for o in occupations:
        wage_str = f"CHF {o['pay_monthly']:,}/mo" if o['pay_monthly'] else "N/A"
        print(f"  {o['isco_code']:4s} {o['title']:65s} {o['jobs']:>8,} jobs  {wage_str}")

    save_csv(occupations)
    save_json(occupations)
