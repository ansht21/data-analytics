# Contributing to Data Analytics Projects

## 🗂️ Project Structure
Each sub-project follows this layout:
```
project-name/
├── data/           # Raw & cleaned datasets
├── sql/            # SQL queries
├── src/            # Python scripts
├── image/          # Generated charts & screenshots
├── excel_analysis/ # Dashboard workbooks (.xlsm/.xlsx)
└── README.md       # Project documentation
```

## 🔧 Setup
1. Clone the repo: `git clone https://gitlab.com/ansht_121/data-analytics.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run any analysis: `python <project>/src/<script_name>.py`

## 📊 Analysis Standards
- Every number in the README must be traceable to committed code
- Negative findings ("don't act") are reported honestly
- SQL queries use CTEs for readability
- All dashboards follow the executive purple card-based UI theme

## 🔄 Workflow
1. Create a feature branch from `main`
2. Make your changes
3. Submit a Merge Request using the provided template
4. Ensure the CI pipeline passes
