# AI Auto-Applier Agent (Groq Edition)

**Status:** ✅ Phase 1-2 Complete | 🚧 Phase 3-6 In Progress

Autonomous job application system combining intelligent job discovery, RAG-powered Q&A, and browser automation (upcoming).

---

## 🎯 What's Built

### ✅ Phase 1: Job Discovery Engine
- Aggregates jobs from **LinkedIn, Indeed, Glassdoor** via python-jobspy
- **STRICT** ATS filtering: Only Greenhouse, Lever, Ashby URLs
- MD5-based deduplication (no repeated applications)
- CSV-based job database with timestamps

### ✅ Phase 2: Memory Layer (RAG System)
- Groq LLM (Llama 3.3 70B) integration for intelligent Q&A
- ChromaDB vector storage with HuggingFace embeddings
- 3-tier answer system: Static → Vector Search → LLM
- Confidence scoring (0.95 static, 0.85 LLM-generated)
- Profile ingestion from JSON + unstructured text

---

## 📋 Prerequisites

- **Python 3.12** (tested with 3.12.0) - **NOT 3.14** (incompatible with ChromaDB)
- pip (Python package manager)
- Groq API key (free tier available)
- Internet connection

---

## 🚀 Quick Start

### 1. Setup Virtual Environment (Python 3.12 Required!)
```bash
# IMPORTANT: Use Python 3.12.x (NOT 3.14 - incompatible with ChromaDB)
python -m venv venv

# Activate
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install all dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Groq API Key
```bash
# Create .env from template
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and add your key:
# GROQ_API_KEY=gsk_your_key_here
```

### 3. Run Phase 1 - Job Discovery
```bash
python main.py
# Output: data/jobs.csv with ATS-filtered jobs
```

### 4. Run Phase 2 - Memory Training & Q&A Test
```bash
python memory\brain.py
# Downloads embeddings (~90MB first time)
# Trains ChromaDB with profile data
# Tests Q&A system with sample questions
```

### 5. Run Phase 3 - Vision Agent (Local Test)
```bash
# Ensure Playwright browsers are installed once
playwright install chromium

# Run the vision integration test (opens browser)
python browser\test_vision.py
# Saves debug_screenshot.png and prints detected fields
```

### 6. Run Phase 4 - API Server
```bash
# Start the FastAPI server (dev)
python -m server.api
# OR with uvicorn
uvicorn server.api:app --reload --host 0.0.0.0 --port 8000

# WebSocket endpoint: ws://localhost:8000/ws
# API docs: http://localhost:8000/docs
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

### Python Version Issues
**Error: ChromaDB/Pydantic installation fails**
```bash
# You MUST use Python 3.12.x (NOT 3.14)
# Pydantic V1 is incompatible with Python 3.14
python --version  # Should show 3.12.x

# Recreate venv with correct version:
deactivate
python3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### GROQ_API_KEY Not Found
```bash
# Create .env from template
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Get free key: https://console.groq.com/keys
# Add to .env: GROQ_API_KEY=gsk_your_key_here
```

### ChromaDB Embeddings Slow on First Run
- **Expected**: First run downloads model (~90MB)
- **Subsequent runs**: Uses cached model (fast)
- **Be patient**: Initial `train_brain()` takes 1-2 minutes

### No Jobs Found (Phase 1)
- Check internet connection
- Try broader search terms ("AI Engineer" vs "Senior Generative AI Specialist")
- Increase `results_wanted` in main.py
- Verify ATS providers aren't blocking your IP (rare)

### Virtual Environment Activation Fails (Windows)
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\activate
```

---

## 📈 Logging & Monitoring

All operations are logged with timestamps. Monitor console output for:
- ✅ Jobs scraped count (Phase 1)
- ✅ ATS filtering results (Phase 1)
- ✅ Brain training progress (Phase 2)
- ✅ Question answering pipeline (Phase 2)
- ⚠️ Warnings (e.g., missing fields)
- ❌ Errors (e.g., network issues)

---

## 🔮 Roadmap

Console logs show:
- **Phase 1**: Jobs scraped, ATS filtering, deduplication stats
- **Phase 2**: Brain training progress, Q&A responses with confidence scores
- **Warnings**: Missing fields, API errors (non-blocking)

---

## 🗺️ Roadmap

### ✅ Phase 0: Setup (Complete)
- [x] Python 3.12 virtual environment
- [x] Dependency management (requirements.txt)
- [x] Groq API integration

### ✅ Phase 1: Job Discovery (Complete)
- [x] Multi-site scraping (LinkedIn, Indeed, Glassdoor)
- [x] ATS filtering (Greenhouse, Lever, Ashby)
- [x] MD5 deduplication system
- [x] CSV database with timestamps

### ✅ Phase 2: Memory Layer (Complete)
- [x] ChromaDB vector storage
- [x] Profile ingestion (JSON + text)
- [x] Intelligent Q&A with Groq LLM
- [x] Confidence scoring system
- [x] JSON-first API design

### ✅ Phase 3: Browser Automation (Complete)
- [x] Playwright async browser (`browser/vision_agent.py`)
- [x] Shadow DOM flattener (`SHADOW_DOM_SCRIPT`) and field detection
- [x] Stealth headers & random delays
- [x] Form filler and screenshot callback

### ✅ Phase 4: Manager & API (Complete)
- [x] `server/orchestrator.py` (`JobOrchestrator`) for the main loop
- [x] `server/api.py` (FastAPI + WebSocket) with `/start`, `/stop`, `/submit`, `/status` and `/ws`
- [x] Human-in-the-loop pause/resume implemented (asyncio.Event)

### 🚧 Phase 5: Human-in-the-Loop (In Progress)
- [x] Interrupt/pause logic for low-confidence answers
- [ ] Learning: Append validated user input to profile and retrain

### 🚀 Phase 6: Polish & Deployment (Planned)
- [ ] Advanced stealth (ghost-cursor)
- [ ] Next.js dashboard and CI/CD deployment

See [docs/roadmap.md](docs/roadmap.md) for detailed milestones.

---

## 📚 Documentation

- [Phase 2 Memory Guide](docs/PHASE2_MEMORY.md) - RAG system deep dive
- [Product Requirements](docs/PRD.md) - Complete feature specifications
- [Roadmap](docs/roadmap.md) - Development timeline

---

## 🤝 Contributing

Future enhancements welcome:
- Additional ATS providers (Workday, iCIMS)
- More job boards integration
- Advanced filtering (salary, remote, etc.)
- Export formats (JSON, Excel)

---

## 📄 License

MIT License

---

## 👨‍💻 Credits

**Built by:** Shubham Kumar (Lead Python Backend Engineer)  
**Specialization:** Data Pipelines, Web Scraping, AI Agents

---

## 🙏 Acknowledgments

- **python-jobspy** - Multi-site job aggregation
- **Groq** - Ultra-fast LLM inference (Llama 3.3 70B)
- **ChromaDB** - Embedded vector database
- **HuggingFace** - Sentence transformers embeddings

---

**Happy Job Hunting! 🎯**

For detailed guides, see [docs/](docs/) directory.

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
