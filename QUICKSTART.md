# 🚀 Quick Start Guide - AI Auto-Applier Agent

## One-Command Setup (Windows)

```powershell
# Run automated setup
.\setup.ps1
```

This will:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup `.env` file

---

## Manual Setup (All Platforms)

### 1. Create Virtual Environment
```bash
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy template
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env and add your Groq API key
# Get from: https://console.groq.com/keys
```

---

## ✅ Phase 1: Job Discovery

### Test Job Scraping
```bash
python main.py
```

**Expected Output:**
```
2026-01-06 15:00:31 - INFO - Starting AI Auto-Applier Agent
2026-01-06 15:00:32 - INFO - Scraping jobs from LinkedIn, Indeed, Glassdoor...
2026-01-06 15:00:45 - INFO - Scraped 150 total jobs
2026-01-06 15:00:45 - INFO - After ATS filtering: 23 jobs
2026-01-06 15:00:45 - INFO - CYCLE COMPLETE: 23 new jobs discovered
```

**Output File:** `data/jobs.csv`

---

## 🧠 Phase 2: Memory Layer (RAG)

### 1. Edit Your Profile

**Static Data** (`data/static_profile.json`):
```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "skills": ["Python", "AI/ML", "RAG"]
}
```

**Stories** (`data/profile_stories.txt`):
- Write 3-4 paragraphs about:
  - Challenging projects
  - Leadership experience
  - Weaknesses and growth
  - Why you're passionate about AI

### 2. Train the Brain
```bash
python memory/brain.py
```

**Expected Output:**
```
[1/3] Training brain with profile_stories.txt...
✓ Split into 15 chunks
✓ Brain training complete. 15 chunks stored in ChromaDB.

[2/3] Testing static profile queries...
Q: What is your email?
A: your.email@example.com
Confidence: 0.95 | Source: static_profile

[3/3] Testing narrative questions (RAG)...
Q: Tell me about a challenging project
A: I led the development of a production RAG system...
Confidence: 0.82 | Source: llm_generated
```

### 3. Interactive Testing
```python
from memory.brain import BrainAgent

brain = BrainAgent()
brain.train_brain()  # One-time training

# Ask questions
response = brain.ask_brain("Why do you want this job?")
print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
```

---

## 📊 Verify Installation

### Check All Components
```bash
# Phase 1: Job Hunter
python -c "from scrapers.hunter import JobHunter; print('✓ Phase 1 OK')"

# Phase 2: Brain Agent
python -c "from memory.brain import BrainAgent; print('✓ Phase 2 OK')"

# Dependencies
python -c "import pandas, pydantic, chromadb, langchain_groq; print('✓ All deps OK')"
```

---

## 🎯 Usage Workflow

### Daily Job Discovery
```bash
# Run every morning
python main.py

# Check results
# data/jobs.csv will have new ATS-compliant jobs
```

### Application Form Filling
```python
from memory.brain import BrainAgent

brain = BrainAgent()

# Common questions
questions = [
    "What is your email?",
    "Why do you want this job?",
    "Tell me about your greatest achievement",
    "What are your strengths?",
]

for q in questions:
    response = brain.ask_brain(q, job_context="AI Engineer at StartupXYZ")
    
    if response.confidence > 0.7:
        print(f"✓ Auto-fill: {response.answer}")
    else:
        print(f"⚠ Manual review needed: {response.answer}")
```

---

## 🔧 Common Commands

### Update Profile
```bash
# After editing profile files
python -c "from memory.brain import BrainAgent; b = BrainAgent(); b.train_brain()"
```

### View Job Stats
```bash
python -c "import pandas as pd; df = pd.read_csv('data/jobs.csv'); print(f'Total jobs: {len(df)}'); print(df['ats_provider'].value_counts())"
```

### Export Jobs to JSON
```bash
python -c "import pandas as pd; df = pd.read_csv('data/jobs.csv'); df.to_json('jobs.json', orient='records', indent=2)"
```

---

## 🐛 Troubleshooting Quick Fixes

### "Module not found"
```bash
# Ensure venv is activated
pip install -r requirements.txt --upgrade
```

### "GROQ_API_KEY not found"
```bash
# Windows
$env:GROQ_API_KEY="gsk_your_key"

# macOS/Linux
export GROQ_API_KEY="gsk_your_key"
```

### "No jobs found"
- Check internet connection
- Try broader search terms
- Verify ATS URLs are not being over-filtered

### ChromaDB errors
```bash
# Delete and retrain
Remove-Item -Recurse -Force chroma_db  # Windows
rm -rf chroma_db                        # macOS/Linux

python memory/brain.py
```

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Main project overview |
| [docs/PHASE2_MEMORY.md](docs/PHASE2_MEMORY.md) | RAG system deep dive |
| [docs/PRD.md](docs/PRD.md) | Product requirements |
| [docs/roadmap.md](docs/roadmap.md) | Development roadmap |

---

## 🎓 Learning Resources

### Understanding the Code
- **JobHunter** (`scrapers/hunter.py`): Web scraping + ATS filtering
- **BrainAgent** (`memory/brain.py`): RAG pipeline (retrieve → reason → respond)

### Key Technologies
- **python-jobspy**: Multi-site job scraping
- **ChromaDB**: Vector database for semantic search
- **Groq**: Fast LLM inference (Llama 3.3)
- **LangChain**: LLM orchestration framework

---

## 🎯 Next Steps

1. ✅ **Phase 1**: Discover jobs → `python main.py`
2. ✅ **Phase 2**: Train your profile → `python memory/brain.py`
3. 🚧 **Phase 3**: Build Next.js dashboard
4. 🚧 **Phase 4**: Automate form filling with Selenium

---

## 🤝 Support

- **Logs**: Check console output with timestamps
- **Issues**: Review docs/PHASE2_MEMORY.md troubleshooting section
- **API Keys**: Get Groq key at https://console.groq.com/keys

---

**Built with ❤️ for AI Engineers | Production-Ready | API-First Design**
