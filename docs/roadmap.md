# Roadmap: AI Auto-Applier Agent (Groq Edition)

**Goal:** Build an autonomous agent that scrapes job boards, analyzes complex forms using Vision/LLMs (Groq Llama 3), and applies automatically with a human-in-the-loop memory system.

**Status:** ✅ Phase 0-4 Complete | 🔧 Phase 5 In Progress | 🚀 Phase 6 Planned

---

## ✅ Phase 0: Setup & Infrastructure (COMPLETE)
*Foundational setup to ensure all tools are ready.*

- [x] **Step 0.1:** Initialize Python Environment.
    - ✅ Created `venv` with Python 3.12.0
    - ✅ Installed all dependencies (100+ packages)
    - ✅ Playwright installed and browsers provisioned (Phase 3 completed)
- [x] **Step 0.2:** API Key Configuration.
    - ✅ Groq API Key configured in `.env`
    - ✅ Using Llama 3.3 70B Versatile model
- [x] **Step 0.3:** Directory Structure.
    - ✅ Created: `scrapers/`, `memory/`, `data/`, `docs/`
    - ✅ Created: `static_profile.json`, `profile_stories.txt`
    - 📝 `browser/` pending (Phase 3)

---

## ✅ Phase 1: The Hunter (Job Aggregation) (COMPLETE)
*Goal: Get a stream of valid URLs to apply to.*

- [x] **Step 1.1:** Basic Scraper Implementation.
    - ✅ Implemented `scrapers/hunter.py` using `python-jobspy`
    - ✅ Configured for LinkedIn/Indeed/Glassdoor scraping
    - ✅ Test: "Generative AI Engineer" in "India"
- [x] **Step 1.2:** Filtering Logic.
    - ✅ **STRICT** filtering: Only `greenhouse.io`, `lever.co`, `ashbyhq.com`
    - ✅ Discards LinkedIn Easy Apply and Workday URLs
    - ✅ MD5-based job ID generation
- [x] **Step 1.3:** Deduplication.
    - ✅ CSV-based deduplication (`jobs.csv`)
    - ✅ Idempotent saves (no duplicates)
    - ✅ Tracks job_id, company, title, url, date

---

## ✅ Phase 2: The Brain (Memory & RAG) (COMPLETE)
*Goal: Stop the agent from hallucinating or asking repetitive questions.*

- [x] **Step 2.1:** Knowledge Base Setup.
    - ✅ Created `memory/brain.py` with `BrainAgent` class
    - ✅ Implemented `train_brain()`: Chunks text into 500-char segments (50 overlap)
    - ✅ **Verified:** `chroma_db/` folder created with 14 chunks
    - ✅ Uses HuggingFace `all-MiniLM-L6-v2` embeddings
- [x] **Step 2.2:** Groq Integration (Text).
    - ✅ Implemented `ask_brain(query)` using `ChatGroq` (Llama 3.3 70B)
    - ✅ 3-Tier Logic: Static → Vector Search (k=3) → LLM Generation
    - ✅ Returns `BrainResponse` with confidence scores (0.95 static, 0.85 LLM)
    - ✅ Fixed `.env` loading with `dotenv`
- [x] **Step 2.3:** Static Data Handler.
    - ✅ `static_profile.json` with 12 skills, 2 education entries
    - ✅ Field mappings: name, email, phone, linkedin, github, experience, skills
    - ✅ Saves LLM tokens on exact-match queries

---

## 👁️ Phase 3: The Vision Agent (Browser Logic) (COMPLETE)
*Goal: The core mechanics of reading and filling forms.*

- [x] **Step 3.1:** Playwright Base.
    - ✅ Implemented `browser/vision_agent.py` using `playwright.async_api`.
    - ✅ Stealth headers with randomized `User-Agent` via `fake-useragent`.
- [x] **Step 3.2:** The Shadow DOM Flattener.
    - ✅ Implemented `SHADOW_DOM_SCRIPT` (JS flattener) and integrated it into `scan_page()`.
    - ✅ `page.evaluate(SHADOW_DOM_SCRIPT)` returns form field maps including Shadow DOM inputs.
- [x] **Step 3.3:** Selector Mapping (The "Eyes").
    - ✅ `scan_page()` produces `selector` and `label` for each field to drive filling logic.
    - ✅ Ready for LLM-driven selector refinement in future iterations.
- [x] **Step 3.4:** Form Filler (The "Hands").
    - ✅ Implemented `fill_form()` and `click_button()` with file upload support.
    - ✅ Observability: `screenshot_callback` streams base64 screenshots to the API WebSocket.

---

## 🎮 Phase 4: The Manager (Integration) (COMPLETE)
*Goal: Tie Hunter, Brain, and Vision together into a loop and expose an API.*

- [x] **Step 4.1:** Main Loop Logic.
    - ✅ Implemented `server/orchestrator.py` (`JobOrchestrator`) to process jobs sequentially.
    - ✅ Flow: `Hunter -> Vision (navigate/scan) -> Brain -> Human-in-the-loop (if needed) -> Fill -> Submit`.
- [x] **Step 4.2:** Error Handling & Resilience.
    - ✅ Orchestrator uses try/except, logs errors, and continues processing.
    - ✅ Stats and progress emitted via WebSocket events.
- [x] **Step 4.3:** API & Observability.
    - ✅ Implemented `server/api.py` (FastAPI) with endpoints `/start`, `/stop`, `/submit` and `/status`.
    - ✅ WebSocket `/ws` broadcasts `log`, `screenshot`, `request_input`, `state`, and `stats` events.

---

## 🛑 Phase 5: The "Human-in-the-Loop" (In Progress)
*Goal: Handle unknown questions gracefully with human oversight.*

- [x] **Step 5.1:** Interrupt Logic (PAUSE/RESUME).
    - ✅ Implemented in `server/orchestrator.py` with `asyncio.Event()` for pause/wait-for-input.
    - ✅ Orchestrator emits `request_input` via WebSocket and awaits `submit_override` (POST /submit) or WS "submit_input".
- [ ] **Step 5.2:** Learning (Pending).
    - ⏳ Plan: Append validated user input to `profile_stories.txt` and re-run `train_brain()` to reinforce answers.
    - ✅ Design specified; implementation planned for Phase 5.2.

---

## 🚀 Phase 6: Polish & Deployment (Planned)
- [ ] **Step 6.1:** Advanced Stealth.
    - Integrate `ghost-cursor` or equivalent for human-like mouse movement.
    - Add configurable random delays and anti-bot mitigations.
- [ ] **Step 6.2:** Dashboard & UX.
    - Build a Next.js dashboard to view `jobs.csv`, screenshots, and real-time events (WS).
- [ ] **Step 6.3:** CI/CD & Deployment.
    - Prepare Docker images and deployment pipelines for production.