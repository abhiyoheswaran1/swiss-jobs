"""
Build site/data.json by merging occupations.json + scores.json.
"""
import json
import os

ROOT = os.path.dirname(__file__)


def main():
    with open(os.path.join(ROOT, "occupations.json")) as f:
        occupations = json.load(f)

    with open(os.path.join(ROOT, "scores.json")) as f:
        scores = json.load(f)

    data = []
    total_jobs = 0
    for occ in occupations:
        slug = occ["slug"]
        score_info = scores.get(slug, {"exposure": 5, "rationale": ""})

        entry = {
            "title": occ["title"],
            "slug": slug,
            "isco_code": occ["isco_code"],
            "category": occ["category"],
            "jobs": occ["jobs"],
            "pay": occ.get("pay_monthly"),
            "pay_annual": occ.get("pay_annual"),
            "education": occ["education"],
            "education_level": occ["education_level"],
            "exposure": score_info["exposure"],
            "exposure_rationale": score_info["rationale"],
        }
        data.append(entry)
        total_jobs += occ["jobs"]

    out_path = os.path.join(ROOT, "site", "data.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote {len(data)} occupations to {out_path}")
    print(f"Total jobs represented: {total_jobs:,}")


if __name__ == "__main__":
    main()
