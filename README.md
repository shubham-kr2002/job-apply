# AI Auto-Applier Agent (Groq Edition) - Phase 1

**Job Discovery Module**: Automated job aggregation, ATS filtering, and deduplication system for AI/ML engineering positions.

---

## 🎯 Overview

Phase 1 implements an intelligent job discovery engine that:
- Aggregates jobs from **LinkedIn, Indeed, and Glassdoor**
- Filters for **ATS-compliant** job boards only (Greenhouse, Lever, Ashby)
- Prevents duplicates using MD5 hashing
- Maintains stealth with randomized headers
- Logs all operations with timestamps

---

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection for job scraping

---

## 🚀 Quick Start

### 1. Clone/Navigate to Project Directory
```bash
cd job-hunter
```

### 2. Create Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate venv
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

**Phase 1 (Job Discovery):**
```bash
python main.py
```

**Phase 2 (Memory Layer - RAG System):**
```bash
# Set your Groq API key first
copy .env.example .env  # Then edit .env with your key

# Test the brain agent
python memory/brain.py
```

---

## 📁 Project Structure

```
job-hunter/
├── main.py                      # Phase 1: Entry point
├── requirements.txt             # Python dependencies (Phase 1 + 2)
├── README.md                    # This file
├── .env.example                 # Environment variables template
├── scrapers/
│   ├── __init__.py
│   └── hunter.py               # JobHunter class (job aggregation)
├── memory/                      # Phase 2: RAG system
│   ├── __init__.py
│   └── brain.py                # BrainAgent class (Q&A)
├── data/
│   ├── jobs.csv                # Phase 1 output (discovered jobs)
│   ├── static_profile.json     # Phase 2: Structured profile data
│   └── profile_stories.txt     # Phase 2: Unstructured bio/stories
├── chroma_db/                   # Phase 2: Vector store (auto-generated)
├── docs/
│   ├── PHASE2_MEMORY.md        # Phase 2 detailed guide
│   ├── PRD.md                  # Product requirements
│   └── roadmap.md              # Development roadmap
└── venv/                        # Virtual environment
```

---

## 🔧 Configuration

### Current Search Parameters (in `main.py`)
- **Search Term**: "Generative AI Engineer"
- **Location**: "India"
- **Results per Site**: 50
- **Time Window**: Last 72 hours

### Modify Search
Edit [main.py](main.py):
```python
search_term = "Your Job Title"
location = "Your Location"
results_per_site = 100  # Adjust as needed
```

---

## 🎨 Features

### ✅ Implemented

#### **Phase 1: Job Discovery**
| Feature | Description | PRD Reference |
|---------|-------------|---------------|
| **Job Aggregation** | Scrapes LinkedIn, Indeed, Glassdoor using `python-jobspy` | FR-1.1 |
| **ATS Filtering** | STRICT filter - only `greenhouse.io`, `lever.co`, `ashbyhq.com` | FR-1.2 |
| **Deduplication** | MD5 hash-based ID system prevents duplicates | FR-1.3 |
| **Schema Validation** | Pydantic models ensure data integrity | Technical Constraint |
| **Observability** | Timestamped logging (no print statements) | Technical Constraint |
| **Idempotency** | Safe to run multiple times - no duplicate data | Technical Constraint |
| **Stealth Headers** | Randomized User-Agent rotation | FR-2.4 (Preliminary) |

#### **Phase 2: Memory Layer (RAG System)** 🆕
| Feature | Description | PRD Reference |
|---------|-------------|---------------|
| **Profile Ingestion** | Loads `static_profile.json` + `profile_stories.txt` into vector store | FR-3.1 |
| **Intelligent Q&A** | Answers job questions using ChromaDB + Groq (Llama 3.3 70B) | FR-3.2 |
| **JSON Responses** | Structured output with `answer`, `confidence`, `reasoning` | UI Requirement |
| **Multi-Tier Lookup** | Static profile → Vector search → LLM generation | Architecture |
| **Confidence Scoring** | 0.0-1.0 scores for manual override support | UI Requirement |
| **Local Embeddings** | HuggingFace `all-MiniLM-L6-v2` (no API calls) | Technical Stack |
| **Type Safety** | Pydantic models for API integration | Technical Constraint |

📖 **Detailed Guide:** See [docs/PHASE2_MEMORY.md](docs/PHASE2_MEMORY.md)

---

## 📊 Output Format

Results are saved to `data/jobs.csv` with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | MD5 hash of company + title (unique identifier) |
| `title` | string | Job title |
| `company` | string | Company name |
| `job_url` | string | Direct link to job posting |
| `location` | string | Job location |
| `date_posted` | string | When job was posted |
| `ats_provider` | string | ATS system (greenhouse.io, lever.co, ashbyhq.com) |

### Example CSV Output
```csv
id,title,company,job_url,location,date_posted,ats_provider
a3f5e1b...,Senior AI Engineer,TechCorp,https://boards.greenhouse.io/...,Bangalore,2026-01-05,greenhouse.io
b9d2c4a...,ML Engineer,StartupXYZ,https://jobs.lever.co/...,Mumbai,2026-01-04,lever.co
```

---

## 🔄 Usage Workflow

1. **First Run**: Scrapes jobs and creates `data/jobs.csv`
2. **Subsequent Runs**: Only adds NEW jobs (deduplication via MD5 hash)
3. **Review Data**: Open `data/jobs.csv` in Excel/Sheets or use pandas

### Example Usage
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Run discovery cycle
python main.py

# Output will show:
# - Number of jobs scraped
# - Number passing ATS filter
# - Number of new jobs saved
# - Total jobs in database
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python-jobspy` | Latest | Multi-site job scraping engine |
| `pandas` | Latest | Data manipulation and CSV operations |
| `pydantic` | Latest | Schema validation and data models |
| `python-dotenv` | Latest | Environment variable management (future use) |

Install all at once:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🛡️ ATS Provider Filtering

**STRICT MODE**: Only jobs from these ATS providers are saved:

- ✅ **Greenhouse** (`greenhouse.io`)
- ✅ **Lever** (`lever.co`)
- ✅ **Ashby** (`ashbyhq.com`)

All other job postings are **automatically discarded** during processing.

**Rationale**: These ATS systems are automation-friendly for Phase 2 (Auto-Application).

---

## 🐛 Troubleshooting

### NumPy Compilation Error (Windows)
If you see "ERROR: Unknown compiler(s)" or "Failed to activate VS environment":

**Solution 1 - Upgrade pip and install (Recommended)**:
```bash
# Upgrade pip tools first
pip install --upgrade pip setuptools wheel

# Install with binary wheels only (no compilation)
pip install --only-binary :all: -r requirements.txt
```

**Solution 2 - If Solution 1 Fails**:
```bash
# Install numpy separately first
pip install numpy

# Then install remaining packages
pip install python-jobspy pandas pydantic python-dotenv
```

**Why this happens**: Python 3.14 is very new and some packages may not have prebuilt wheels yet, requiring compilation. The updated requirements.txt now handles this automatically.

### Virtual Environment Not Activating
**Windows**:
```bash
# If script execution is disabled:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\activate
```

**macOS/Linux**:
```bash
# Ensure correct path:
source venv/bin/activate
```

### No Jobs Found
- Check internet connection
- Verify search term is not too specific
- Try broader location (e.g., "United States" instead of "Small Town, TX")
- Increase `results_wanted` parameter

### ImportError After Installation
```bash
# Ensure venv is activated (you should see (venv) in terminal)
# Reinstall dependencies:
pip install --upgrade -r requirements.txt
```

### Permission Errors on data/jobs.csv
- Close any programs with the CSV file open (Excel, etc.)
- Ensure `data/` directory exists and is writable

### Phase 2: "GROQ_API_KEY not found"
```bash
# Create .env file from example
copy .env.example .env

# Edit .env and add your Groq API key
# Get key from: https://console.groq.com/keys
```

### Phase 2: ChromaDB/HuggingFace Slow First Run
- First run downloads embedding model (~90MB)
- Subsequent runs use cached model
- Be patient on first `train_brain()` call

---

## 📈 Logging

All operations are logged with timestamps. Monitor console output for:
- ✅ Jobs scraped count (Phase 1)
- ✅ ATS filtering results (Phase 1)
- ✅ Brain training progress (Phase 2)
- ✅ Question answering pipeline (Phase 2)
- ⚠️ Warnings (e.g., missing fields)
- ❌ Errors (e.g., network issues)

---

## 🔮 Roadmap

### Phase 1 ✅ COMPLETE
- [x] Job aggregation from LinkedIn, Indeed, Glassdoor
- [x] ATS filtering (Greenhouse, Lever, Ashby)
- [x] Deduplication with MD5 hashing
- [x] CSV data persistence

### Phase 2 ✅ COMPLETE
- [x] RAG system with ChromaDB + Groq
- [x] Profile ingestion (JSON + unstructured text)
- [x] Intelligent Q&A with confidence scores
- [x] JSON-first API design for Next.js

### Phase 3 (In Progress)
- [ ] Next.js dashboard UI
- [ ] API endpoints (`/api/brain`, `/api/jobs`)
- [ ] Manual override interface
- [ ] Batch question answering

### Phase 4 (Planned)
- [ ] Selenium-based auto-application
- [ ] Resume/CV parsing
- [ ] Form detection and filling
- [ ] Application tracking system

### Phase 3 (Planned)
- [ ] Email monitoring
- [ ] Interview scheduling
- [ ] Follow-up automation

---

## 🤝 Contributing

This is a Phase 1 implementation. Future enhancements welcome:
- Additional ATS providers
- More job boards
- Advanced filtering logic
- Export formats (JSON, Excel)

---

## 📄 License

[Add your license here]

---

## 👨‍💻 Author

Built by a Lead Python Backend Engineer specializing in Data Pipelines and Web Scraping.

---

## 🙏 Acknowledgments

- `python-jobspy` for job aggregation capabilities
- `pydantic` for robust data validation
- Community feedback and testing

---

**Happy Job Hunting! 🎯**

For issues or questions, check the logs and review the troubleshooting section above.
