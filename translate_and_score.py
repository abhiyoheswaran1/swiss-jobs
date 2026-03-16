"""
Translate German occupation titles to English and score AI exposure.
Uses Claude API to do both in one call per occupation.
"""
import json
import os
import sys
import time

SAKE_PATH = os.path.join(os.path.dirname(__file__), "data", "bfs_sake_3digit.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "occupations_translated_scored.json")

PROMPT = """You are translating Swiss occupation titles and scoring AI exposure.

German occupation title: {title_de}
ISCO code: {isco_code}
Employment in Switzerland: {employment:,} workers

Do two things:
1. Translate the German title to a concise English equivalent (max 6 words if possible, keep it natural)
2. Score AI exposure 0-10 following this scale:
   - 0-1: Physical/hands-on (roofer, cleaner)
   - 2-3: Mostly physical (electrician, firefighter)
   - 4-5: Mixed (nurse, veterinarian)
   - 6-7: Knowledge work (teacher, accountant)
   - 8-9: Computer-based (software developer, data analyst)
   - 10: Routine digital (data entry)

Respond with ONLY JSON:
{{"title_en": "...", "exposure": <0-10>, "rationale": "<1 sentence>"}}
"""


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    with open(SAKE_PATH) as f:
        occupations = json.load(f)

    # Load existing results for resume capability
    results = {}
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            existing = json.load(f)
            results = {r["isco_code"]: r for r in existing}

    print(f"Processing {len(occupations)} occupations ({len(results)} already done)...")

    for i, occ in enumerate(occupations):
        code = occ["isco_code"]
        if code in results:
            continue

        prompt = PROMPT.format(**occ)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            data = json.loads(text)

            results[code] = {
                **occ,
                "title_en": data["title_en"],
                "exposure": data["exposure"],
                "exposure_rationale": data["rationale"],
            }
            print(f"  [{i+1}/{len(occupations)}] {code} {data['title_en']}: {data['exposure']}/10")

            # Save incrementally
            with open(OUTPUT_PATH, "w") as f:
                json.dump(list(results.values()), f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"  ERROR {code}: {e}")
            time.sleep(2)

    print(f"\nDone! {len(results)} occupations saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
