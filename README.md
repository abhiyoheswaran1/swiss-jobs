# Swiss Job Market & AI Exposure

Interactive treemap visualization of Swiss occupations and their AI exposure, inspired by [Andrej Karpathy's US Jobs project](https://karpathy.ai/jobs/).

## Overview

Visualizes **38 occupations** covering **4.4 million Swiss jobs** using ISCO-08 classification with three interactive views:

- **Digital AI Exposure** — How much AI will reshape each occupation (0-10 scale)
- **Median Pay** — Monthly gross wages in CHF
- **Education Level** — Required education from no formal to university degree

## Data Sources

- **Employment**: [Eurostat Labour Force Survey](https://ec.europa.eu/eurostat) (lfsa_egai2d, 2023) — employed persons by ISCO-08 two-digit level for Switzerland
- **Wages**: [Swiss Federal Statistical Office (BFS)](https://www.bfs.admin.ch) — Wage Structure Survey (LSE) 2022, median gross monthly wages by occupation group
- **AI Exposure**: Scored using Karpathy's methodology — 0-10 scale based on digital work exposure

## Quick Start

```bash
# Install dependencies
pip install requests pandas anthropic

# Fetch data from Eurostat & BFS
python fetch_data.py

# Process and merge
python process_data.py

# Score AI exposure (uses expert estimates; set ANTHROPIC_API_KEY for Claude-powered scoring)
python score.py

# Build site data
python build_site_data.py

# Serve the site
cd site && python -m http.server 8000
# Open http://localhost:8000
```

## Re-score with Claude API

To use Claude for AI exposure scoring instead of pre-computed estimates:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python score.py
python build_site_data.py
```

## Project Structure

```
swiss-jobs/
├── data/                    # Raw data from APIs
├── site/
│   ├── index.html          # Interactive treemap visualization
│   └── data.json           # Compiled occupation data
├── fetch_data.py           # Eurostat + BFS data fetcher
├── process_data.py         # Data cleaning & merging
├── score.py                # AI exposure scoring
├── build_site_data.py      # Compile site data
├── occupations.csv         # Processed occupation data
├── occupations.json        # Processed occupation data (JSON)
└── scores.json             # AI exposure scores
```

## License

MIT
