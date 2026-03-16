# Swiss Job Market & AI Exposure

Interactive treemap visualization of Swiss occupations and their AI exposure, inspired by [Andrej Karpathy's US Jobs project](https://karpathy.ai/jobs/).

**Live:** [swiss-jobs-ai.web.app](https://swiss-jobs-ai.web.app)

## Overview

Visualizes **135 occupations** covering **4.3 million Swiss jobs** using ISCO-08 3-digit classification with three interactive views:

- **Digital AI Exposure** - How much AI will reshape each occupation (0-10 scale)
- **Median Pay** - Monthly gross wages in CHF
- **Education Level** - Required education from no formal to university degree

Includes an EN/DE language toggle with full German translation of all titles, labels, and descriptions.

## Data Sources

- **Employment**: [Swiss Federal Statistical Office (BFS)](https://www.bfs.admin.ch) - Swiss Labour Force Survey (SAKE) 2019-2021 cumulated, CH-ISCO-19 3-digit level
- **Wages**: [BFS](https://www.bfs.admin.ch) - Wage Structure Survey (LSE) 2022, median gross monthly wages by ISCO-08 2-digit group
- **AI Exposure**: Each occupation scored 0-10 by Claude (Anthropic) following Karpathy's methodology

## Quick Start

```bash
# Install dependencies
pip install requests pandas anthropic

# Fetch employment and wage data from BFS
python fetch_data.py

# Translate German titles to English and score AI exposure (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python translate_and_score.py

# Build site data (merges scores + wages into site/data.json)
python build_site_data.py

# Serve the site
cd site && python -m http.server 8000
# Open http://localhost:8000
```

## Deploy to Firebase

```bash
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

## Project Structure

```
swiss-jobs/
├── data/
│   ├── bfs_sake_3digit.json              # 135 occupations from BFS SAKE
│   ├── bfs_wages.json                    # Wage data by ISCO 2-digit
│   ├── bfs_isco19_detail.xlsx            # Raw BFS SAKE Excel source
│   └── occupations_translated_scored.json # Translated + AI-scored occupations
├── site/
│   ├── index.html                        # Interactive treemap visualization
│   └── data.json                         # Compiled occupation data
├── fetch_data.py                         # BFS API data fetcher
├── process_data.py                       # Data cleaning and merging
├── translate_and_score.py                # Claude API translation + scoring
├── build_site_data.py                    # Compile site data
├── score.py                              # AI exposure scoring (legacy)
├── firebase.json                         # Firebase Hosting config
└── .firebaserc                           # Firebase project config
```

## License

MIT
