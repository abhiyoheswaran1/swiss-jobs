"""
Score Swiss occupations for AI exposure using Claude API.

Uses the same methodology as Karpathy's US jobs project:
- Scale: 0-10 measuring how much AI will reshape each occupation
- Key principle: digital/computer work = higher exposure
- Anchors: roofers (0-1), data entry (10)

Usage:
    python score.py                    # Score all occupations
    python score.py --dry-run          # Show what would be scored without calling API

Requires ANTHROPIC_API_KEY environment variable.
Falls back to pre-computed expert estimates if no API key is available.
"""
import json
import os
import sys

SCORES_PATH = os.path.join(os.path.dirname(__file__), "scores.json")
OCCUPATIONS_PATH = os.path.join(os.path.dirname(__file__), "occupations.json")

SCORING_PROMPT = """You are an expert analyzing occupational exposure to AI disruption.

Score the following occupation on a scale of 0-10 for "Digital AI Exposure" — how fundamentally AI will reshape this occupation over the next 5-10 years.

Key principle: Work done entirely on computers faces the highest AI exposure.

Score anchors:
- 0-1: Purely physical/hands-on work (roofer, construction laborer, landscaper)
- 2-3: Mostly physical with minor AI support (electrician, firefighter, plumber)
- 4-5: Mixed physical/knowledge work (nurse, veterinarian, police officer)
- 6-7: Predominantly knowledge/office work (teacher, accountant, marketing manager)
- 8-9: Almost entirely computer-based (software developer, graphic designer, data analyst)
- 10: Routine digital processing (data entry clerk, basic bookkeeping)

Important: High scores do NOT predict job disappearance. They indicate the degree of AI-driven transformation, including productivity gains, task automation, and workflow changes.

Occupation: {title}
ISCO Code: {isco_code}
Category: {category}
Typical Education: {education}
Employment in Switzerland: {jobs:,} workers
Median Monthly Wage: CHF {pay_monthly:,}

Respond with ONLY a JSON object:
{{"exposure": <0-10 integer>, "rationale": "<2-3 sentences explaining the score>"}}
"""

# Pre-computed expert estimates following Karpathy's methodology
# These are used as fallback when no API key is available
EXPERT_SCORES = {
    "11": {"exposure": 6, "rationale": "Chief executives and legislators increasingly rely on AI for data-driven decision making, strategic analysis, and communication. However, leadership, negotiation, and stakeholder management remain deeply human. Moderate-high reshaping of analytical and administrative aspects."},
    "12": {"exposure": 7, "rationale": "Administrative and commercial managers work predominantly in digital environments — finance, HR, marketing, operations. AI tools are already automating reporting, forecasting, and workflow management. Significant transformation of day-to-day managerial tasks."},
    "13": {"exposure": 6, "rationale": "Production and specialized services managers oversee physical operations but spend significant time on planning, scheduling, and analysis. AI will reshape the analytical side while physical oversight remains human-driven."},
    "14": {"exposure": 4, "rationale": "Hospitality and retail managers deal extensively with in-person customer interactions, staff management, and physical operations. AI helps with scheduling and inventory but the core role requires human presence and interpersonal skills."},
    "21": {"exposure": 8, "rationale": "Science and engineering professionals work heavily with computation, modeling, and data analysis — all areas where AI excels. AI coding assistants, simulation tools, and automated analysis are transforming daily workflows. High digital exposure."},
    "22": {"exposure": 4, "rationale": "Health professionals combine knowledge work with physical patient care. AI will assist with diagnostics, treatment planning, and documentation, but hands-on care, empathy, and complex clinical judgment remain central."},
    "23": {"exposure": 5, "rationale": "Teaching professionals combine knowledge delivery with interpersonal mentoring and classroom management. AI will transform content creation, grading, and personalized learning, but the human connection in education remains essential."},
    "24": {"exposure": 8, "rationale": "Business and administration professionals work almost entirely on computers — financial analysis, consulting, compliance, auditing. AI is already automating report generation, data analysis, and routine advisory work. Very high digital exposure."},
    "25": {"exposure": 9, "rationale": "ICT professionals are at the epicenter of AI transformation. AI coding assistants, automated testing, and AI-driven development are fundamentally reshaping software development, system administration, and IT operations. Paradoxically, the profession building AI is most exposed to it."},
    "26": {"exposure": 7, "rationale": "Legal, social, and cultural professionals — lawyers, economists, journalists, artists — work primarily with text, analysis, and creative output. AI is rapidly advancing in legal research, writing, translation, and creative generation."},
    "31": {"exposure": 6, "rationale": "Science and engineering technicians bridge theory and practice — lab work, technical drawing, quality control. AI assists with analysis and documentation, but much work involves physical equipment operation and on-site technical tasks."},
    "32": {"exposure": 4, "rationale": "Health associate professionals (nurses, paramedics, dental hygienists) primarily provide hands-on patient care. AI may assist with monitoring and documentation, but the physical and empathetic care components keep exposure moderate."},
    "33": {"exposure": 8, "rationale": "Business and administration associate professionals handle bookkeeping, insurance processing, real estate, and administrative coordination — mostly computer-based tasks that AI can significantly automate or augment."},
    "34": {"exposure": 5, "rationale": "Legal, social, and cultural associate professionals include social workers, sports coaches, and religious workers. Many roles involve significant face-to-face interaction and community engagement, limiting AI's direct impact."},
    "35": {"exposure": 7, "rationale": "ICT technicians handle network operations, user support, and system maintenance. AI-powered monitoring, automated troubleshooting, and self-healing systems are transforming these roles, though physical hardware work remains."},
    "41": {"exposure": 9, "rationale": "General and keyboard clerks perform data entry, typing, filing, and administrative processing — quintessentially routine digital tasks. AI can automate most of these functions, making this one of the most exposed occupation groups."},
    "42": {"exposure": 7, "rationale": "Customer services clerks handle inquiries, bookings, and front-desk tasks. AI chatbots and automated systems are already replacing many of these functions, though complex or emotionally sensitive interactions still require humans."},
    "43": {"exposure": 8, "rationale": "Numerical and material recording clerks handle accounting, stock-keeping, and statistical work — routine data processing tasks well-suited for AI automation. Spreadsheet work, data reconciliation, and record-keeping are prime automation targets."},
    "44": {"exposure": 7, "rationale": "Other clerical support workers handle mail, coding, proofreading, and miscellaneous office tasks. Many of these routine administrative functions can be automated by AI document processing and workflow tools."},
    "51": {"exposure": 3, "rationale": "Personal service workers — cooks, waiters, hairdressers, travel guides — work primarily in physical, face-to-face settings. AI has limited impact on hands-on service delivery, though booking and ordering systems are being automated."},
    "52": {"exposure": 5, "rationale": "Sales workers combine product knowledge with customer interaction. AI is transforming e-commerce and personalized recommendations, but in-store retail still relies on human engagement. Mixed exposure across physical and digital channels."},
    "53": {"exposure": 3, "rationale": "Personal care workers — childcare, elderly care, healthcare assistants — provide hands-on physical and emotional care. This deeply human work has very limited AI exposure, though scheduling and documentation may be assisted."},
    "54": {"exposure": 3, "rationale": "Protective services workers — police, firefighters, security guards — work in physical environments requiring real-time judgment and physical intervention. AI assists with surveillance and analysis but cannot replace the physical presence."},
    "61": {"exposure": 2, "rationale": "Agricultural workers operate in outdoor physical environments — planting, harvesting, animal husbandry. While precision agriculture and AI monitoring are emerging, the core work remains manual and weather-dependent."},
    "62": {"exposure": 2, "rationale": "Forestry, fishery, and hunting workers operate in remote natural environments with highly physical tasks. AI has minimal direct impact on chainsaw operation, fishing, or wildlife management."},
    "71": {"exposure": 2, "rationale": "Building trades workers — masons, carpenters, roofers, painters — perform physical construction work. AI may assist with planning and estimation, but the hands-on craft work in variable environments resists automation."},
    "72": {"exposure": 3, "rationale": "Metal and machinery trades workers — welders, mechanics, toolmakers — combine physical skill with technical knowledge. While CNC and automation affect manufacturing, skilled repair and custom work remain human-driven."},
    "73": {"exposure": 5, "rationale": "Handicraft and printing workers span traditional crafts and digital printing. Print production is already heavily digitized, and AI is impacting graphic design and pre-press work, while artisanal crafts remain manual."},
    "74": {"exposure": 3, "rationale": "Electrical and electronic trades workers install and maintain electrical systems — physical work in buildings and infrastructure. AI assists with diagnostics, but hands-on installation and repair in diverse settings keeps exposure low."},
    "75": {"exposure": 3, "rationale": "Food processing, woodworking, and garment workers perform physical manufacturing tasks. While some factory automation exists, much of Swiss food production and craft manufacturing involves skilled manual work."},
    "81": {"exposure": 4, "rationale": "Stationary plant and machine operators monitor and control industrial equipment. AI-driven process optimization and predictive maintenance are changing these roles, but operators still oversee physical machinery."},
    "82": {"exposure": 4, "rationale": "Assemblers work on production lines combining components. While robotic assembly advances, many Swiss manufacturing tasks require human dexterity and quality judgment. AI impacts planning and quality control more than assembly itself."},
    "83": {"exposure": 3, "rationale": "Drivers and mobile plant operators — truck drivers, bus drivers, crane operators — perform physical tasks in dynamic environments. Autonomous vehicles are developing but widespread deployment in Switzerland remains distant."},
    "91": {"exposure": 1, "rationale": "Cleaners and helpers perform manual cleaning in diverse physical environments — offices, hospitals, homes. This is almost entirely physical work that current AI and robotics cannot effectively automate at scale."},
    "92": {"exposure": 1, "rationale": "Agricultural labourers perform manual farm work — harvesting, sorting, loading. This is physically demanding outdoor work with minimal digital component. AI exposure is very low."},
    "93": {"exposure": 2, "rationale": "Construction, mining, and transport labourers perform heavy manual work — digging, lifting, carrying. AI has very limited impact on these physical tasks, though some logistics optimization may help."},
    "94": {"exposure": 2, "rationale": "Food preparation assistants wash dishes, clean kitchens, and prepare basic ingredients. This is physical work in kitchen environments where AI has minimal direct impact."},
    "96": {"exposure": 2, "rationale": "Refuse workers and other elementary workers — garbage collectors, street sweepers — perform essential physical services. Automation exists for some waste processing, but collection in varied urban environments remains manual."},
}


def score_with_api(occupations):
    """Score occupations using Claude API."""
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed. Run: pip install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)
    scores = {}

    # Load existing scores for caching
    if os.path.exists(SCORES_PATH):
        with open(SCORES_PATH) as f:
            scores = json.load(f)

    for occ in occupations:
        slug = occ["slug"]
        if slug in scores:
            continue

        prompt = SCORING_PROMPT.format(**occ)
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            result = json.loads(text)
            scores[slug] = result
            print(f"  Scored {occ['title']}: {result['exposure']}/10")

            # Save incrementally
            with open(SCORES_PATH, "w") as f:
                json.dump(scores, f, indent=2)

        except Exception as e:
            print(f"  Error scoring {occ['title']}: {e}")

    return scores


def score_with_estimates(occupations):
    """Use pre-computed expert estimates."""
    scores = {}
    for occ in occupations:
        code = occ["isco_code"]
        if code in EXPERT_SCORES:
            scores[occ["slug"]] = EXPERT_SCORES[code]
        else:
            scores[occ["slug"]] = {
                "exposure": 5,
                "rationale": "No specific assessment available for this occupation.",
            }
    return scores


def main():
    dry_run = "--dry-run" in sys.argv

    with open(OCCUPATIONS_PATH) as f:
        occupations = json.load(f)

    print(f"Scoring {len(occupations)} occupations for AI exposure...")

    if dry_run:
        for occ in occupations:
            print(f"  Would score: {occ['isco_code']} {occ['title']}")
        return

    # Try API first, fall back to expert estimates
    scores = score_with_api(occupations)
    if scores is None:
        print("  No ANTHROPIC_API_KEY found. Using pre-computed expert estimates.")
        scores = score_with_estimates(occupations)

    with open(SCORES_PATH, "w") as f:
        json.dump(scores, f, indent=2)

    print(f"\nSaved {len(scores)} scores to {SCORES_PATH}")

    # Distribution summary
    exposure_values = [s["exposure"] for s in scores.values()]
    total_jobs = sum(o["jobs"] for o in occupations)
    weighted = sum(
        scores[o["slug"]]["exposure"] * o["jobs"]
        for o in occupations
        if o["slug"] in scores
    ) / total_jobs
    print(f"Average exposure: {sum(exposure_values)/len(exposure_values):.1f}")
    print(f"Job-weighted exposure: {weighted:.1f}")


if __name__ == "__main__":
    main()
