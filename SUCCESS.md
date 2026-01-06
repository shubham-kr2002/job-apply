# ✅ Installation Complete - Python 3.12

## What We Fixed
**Problem:** Python 3.14 was incompatible with ChromaDB (uses Pydantic V1)
**Solution:** Switched to Python 3.12.0

## Current Status
- ✅ Virtual environment: Python 3.12.0
- ✅ All dependencies installed successfully
- ✅ Phase 1 tests: **PASSING**
- 🔄 Phase 2: Downloading embedding model (first run only)

## Installed Packages
- **Phase 1 (Job Discovery):**
  - numpy 1.26.3
  - pandas 2.3.3
  - python-jobspy 1.1.82
  - pydantic 2.12.5
  
- **Phase 2 (RAG Memory):**
  - chromadb 0.4.24
  - langchain-chroma 0.2.3
  - langchain-groq 1.1.1
  - langchain-core 1.2.6
  - sentence-transformers 5.2.0
  - torch 2.9.1 (110.9 MB)
  - transformers 4.57.3

## Next Steps

### 1. Run Phase 1 (Job Scraping)
```powershell
python main.py
```
This will:
- Search for "Generative AI Engineer" jobs in "India"
- Filter for ATS-compliant URLs (greenhouse.io, lever.co, ashbyhq.com)
- Save results to `data/jobs.csv`

### 2. Train the Brain (Phase 2)
```powershell
python memory\brain.py
```
This will:
- Load your profile from `data/static_profile.json` and `data/profile_stories.txt`
- Create vector embeddings
- Test Q&A functionality
- Save to `chroma_db/` folder

### 3. Customize Your Profile
Edit these files with your real information:
- `data/static_profile.json` - Your name, email, skills, education
- `data/profile_stories.txt` - Your project stories, achievements

### 4. Get More Groq Credits (Optional)
- Current key: `<REDACTED - set in .env>`
- Get more at: https://console.groq.com/keys
- Groq offers a free tier for development

## Testing Commands
```powershell
# Test both phases
python test_system.py

# Test Phase 1 only
python -c "from scrapers.hunter import JobHunter; print('✓ Phase 1 ready')"

# Test Phase 2 only
python -c "from memory.brain import BrainAgent; print('✓ Phase 2 ready')"
```

## File Structure
```
job-hunter/
├── venv/                    # Python 3.12 virtual environment
├── data/
│   ├── static_profile.json  # Your structured profile
│   ├── profile_stories.txt  # Your behavioral stories
│   └── jobs.csv            # Scraped jobs (generated)
├── chroma_db/              # Vector database (generated)
├── scrapers/
│   └── hunter.py           # Phase 1: Job scraping
├── memory/
│   └── brain.py            # Phase 2: RAG Q&A system
├── main.py                 # Phase 1 entry point
├── test_system.py          # Automated test suite
├── .env                    # Groq API key
└── requirements.txt        # All dependencies
```

## Troubleshooting

### If brain.py is slow on first run:
- It's downloading the embedding model (~90MB)
- Only happens once
- Subsequent runs are instant

### If job scraping returns no results:
- JobSpy sometimes gets rate-limited
- Try different search terms
- Try different locations
- Wait a few minutes and retry

### If Groq API key expires:
1. Get new key from https://console.groq.com/keys
2. Update `.env` file: `GROQ_API_KEY=gsk_your_new_key`
3. Restart script

## What's Next? (Phase 3)
After testing Phases 1 & 2:
- Browser automation with Playwright
- Groq Vision for CAPTCHA solving
- Auto-fill job application forms
- Next.js dashboard for monitoring

## Need Help?
Check these docs:
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick commands
- [docs/PHASE2_MEMORY.md](docs/PHASE2_MEMORY.md) - RAG system deep dive
- [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md) - Python 3.14 → 3.12 migration
