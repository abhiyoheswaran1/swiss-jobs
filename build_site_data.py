"""
Build site/data.json from 135 3-digit ISCO occupations.
Merges translated+scored data with BFS wage data.
"""
import json
import os
import re

ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, "data")

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

MAJOR_GROUPS_DE = {
    "0": "Streitkräfte",
    "1": "Führungskräfte",
    "2": "Akademische Berufe",
    "3": "Techniker und gleichrangige Berufe",
    "4": "Bürokräfte und verwandte Berufe",
    "5": "Dienstleistungsberufe und Verkäufer",
    "6": "Fachkräfte in Landwirtschaft und Fischerei",
    "7": "Handwerks- und verwandte Berufe",
    "8": "Anlagen- und Maschinenbediener",
    "9": "Hilfsarbeitskräfte",
}

# Education level typical for each ISCO major group
EDUCATION_BY_MAJOR = {
    "0": ("Military training", "Militärische Ausbildung"),
    "1": ("Bachelor's degree or higher", "Bachelor-Abschluss oder höher"),
    "2": ("Bachelor's degree or higher", "Bachelor-Abschluss oder höher"),
    "3": ("Professional diploma / Higher vocational", "Berufsdiplom / Höhere Fachschule"),
    "4": ("Upper secondary / Vocational", "Sekundarstufe II / Berufslehre"),
    "5": ("Upper secondary / Vocational", "Sekundarstufe II / Berufslehre"),
    "6": ("Upper secondary / Vocational", "Sekundarstufe II / Berufslehre"),
    "7": ("Upper secondary / Vocational", "Sekundarstufe II / Berufslehre"),
    "8": ("Upper secondary or less", "Sekundarstufe II oder weniger"),
    "9": ("No formal education required", "Keine formale Ausbildung erforderlich"),
}

EDUCATION_LEVEL = {
    "No formal education required": 1,
    "Upper secondary or less": 2,
    "Upper secondary / Vocational": 3,
    "Professional diploma / Higher vocational": 4,
    "Bachelor's degree or higher": 5,
    "Military training": 3,
}


def slugify(text):
    s = text.lower()
    s = re.sub(r"[,'.():]", "", s)
    s = re.sub(r"[\s/]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def main():
    # Load scored occupations (135 entries)
    with open(os.path.join(DATA_DIR, "occupations_translated_scored.json")) as f:
        occupations = json.load(f)

    # Load wage data (keyed by 2-digit ISCO)
    with open(os.path.join(DATA_DIR, "bfs_wages.json")) as f:
        wages = json.load(f)

    data = []
    total_jobs = 0
    with_wages = 0

    for occ in occupations:
        code = occ["isco_code"]
        major = occ["major_group"]
        isco_2d = occ["isco_2digit"]

        category = MAJOR_GROUPS.get(major, "Other")
        category_de = MAJOR_GROUPS_DE.get(major, "Andere")
        edu_en, edu_de = EDUCATION_BY_MAJOR.get(major, ("Unknown", "Unbekannt"))

        # Map wage from 2-digit parent
        wage_info = wages.get(isco_2d, {})
        monthly = wage_info.get("median_wage_monthly_chf")
        annual = wage_info.get("median_wage_annual_chf")

        # If no 2-digit match, try 1-digit (major group with leading 1)
        if not monthly:
            wage_info = wages.get(str(int(major) + 10) if major != "0" else "10", {})
            monthly = wage_info.get("median_wage_monthly_chf")
            annual = wage_info.get("median_wage_annual_chf")

        if monthly:
            with_wages += 1

        entry = {
            "title": occ["title_en"],
            "title_de": occ["title_de"],
            "slug": slugify(occ["title_en"]),
            "isco_code": code,
            "category": category,
            "category_de": category_de,
            "jobs": occ["employment"],
            "pay": monthly,
            "pay_annual": annual,
            "education": edu_en,
            "education_de": edu_de,
            "education_level": EDUCATION_LEVEL.get(edu_en, 0),
            "exposure": occ["exposure"],
            "exposure_rationale": occ.get("exposure_rationale", ""),
        }
        data.append(entry)
        total_jobs += occ["employment"]

    # Sort by category then employment descending
    data.sort(key=lambda x: (x["category"], -x["jobs"]))

    out_path = os.path.join(ROOT, "site", "data.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(data)} occupations to {out_path}")
    print(f"Total jobs: {total_jobs:,}")
    print(f"With wage data: {with_wages}/{len(data)}")


if __name__ == "__main__":
    main()
