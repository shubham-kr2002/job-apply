# Roadmap: AI Auto-Applier Agent (Groq Edition)

**Goal:** Build an autonomous agent that scrapes job boards, analyzes complex forms using Vision/LLMs (Groq Llama 3), and applies automatically with a human-in-the-loop memory system.

**Status:** ✅ Phase 0-2 Complete | 🚧 Phase 3-6 In Progress

---

## ✅ Phase 0: Setup & Infrastructure (COMPLETE)
*Foundational setup to ensure all tools are ready.*

- [x] **Step 0.1:** Initialize Python Environment.
    - ✅ Created `venv` with Python 3.12.0
    - ✅ Installed all dependencies (100+ packages)
    - ⚠️ Playwright install pending (Phase 3)
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

## 👁️ Phase 3: The Vision Agent (Browser Logic)
*Goal: The core mechanics of reading and filling forms.*

- [ ] **Step 3.1:** Playwright Base.
    - Create `browser/vision_agent.py`.
    - Setup Async Playwright with stealth headers (`user_agent` rotation).
- [ ] **Step 3.2:** The Shadow DOM Flattener.
    - Implement the JS injection script (`dom_utils.js`) to expand Shadow Roots.
    - Verify: `page.evaluate(FLATTENER_JS)` should return deep HTML including hidden inputs.
- [ ] **Step 3.3:** Selector Mapping (The "Eyes").
    - Function: `get_selectors(html)` -> Sends cleaned HTML to Groq Llama 3.3.
    - Prompt Engineering: Ensure JSON output is strictly formatted `{"field": "selector"}`.
- [ ] **Step 3.4:** Form Filler (The "Hands").
    - Iterate through the map.
    - Handle Text Inputs (`.fill()`) and File Uploads (`.set_input_files()`).

---

## 🎮 Phase 4: The Manager (Integration)
*Goal: Tie Hunter, Brain, and Vision together into a loop.*

- [ ] **Step 4.1:** Main Loop Logic.
    - Create `main.py`.
    - Flow: `Hunter -> List[URLs] -> Loop -> Vision Agent -> Submit`.
- [ ] **Step 4.2:** Error Handling (Try/Except).
    - Wrap the application process. If it crashes, log error to `jobs.csv` and continue to next job.
    - Do not crash the entire script on one failure.
- [ ] **Step 4.3:** Success Validation.
    - Detect "Success" message or URL change (e.g., `/thank-you`).
    - Take a screenshot of the success page.

---

## 🛑 Phase 5: The "Human-in-the-Loop" (Advanced)
*Goal: Handle unknown questions gracefully.*

- [ ] **Step 5.1:** Interrupt Logic.
    - In `vision_agent.py`: If `ask_brain()` returns low confidence or `None`:
        - **PAUSE** Playwright execution.
        - **PRINT** Alert to Console: "USER HELP NEEDED: What is your salary expectation?"
        - **WAIT** for `input()`.
- [ ] **Step 5.2:** Learning.
    - Take the user's `input()`, append it to `profile_stories.txt`, and re-run `train_brain()` instantly.
    - Resume form filling with the new answer.

---

## 🚀 Phase 6: Polish & Deployment
- [ ] **Step 6.1:** Stealth Mode.
    - Integrate `ghost-cursor` for human-like mouse movement.
    - Add random `sleep()` intervals (2s - 5s).
- [ ] **Step 6.2:** Dashboard (Optional).
    - Build a simple Streamlit app to view `jobs.csv` and screenshots.