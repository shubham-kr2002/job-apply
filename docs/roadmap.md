# Roadmap: AI Auto-Applier Agent (Groq Edition)

**Goal:** Build an autonomous agent that scrapes job boards, analyzes complex forms using Vision/LLMs (Groq Llama 3), and applies automatically with a human-in-the-loop memory system.

---

## 📅 Phase 0: Setup & Infrastructure
*Foundational setup to ensure all tools are ready.*

- [ ] **Step 0.1:** Initialize Python Environment.
    - Create `venv`.
    - Install `requirements.txt` (Playwright, LangChain, Groq, ChromaDB).
    - Run `playwright install`.
- [ ] **Step 0.2:** API Key Configuration.
    - Get **Groq API Key** (Free tier for Llama 3 models).
    - Create `.env` file (`GROQ_API_KEY=...`).
- [ ] **Step 0.3:** Directory Structure.
    - Create folders: `scrapers/`, `memory/`, `browser/`, `data/`.
    - Create dummy `resume.pdf` and `profile.txt` in `data/`.

---

## 🕵️ Phase 1: The Hunter (Job Aggregation)
*Goal: Get a stream of valid URLs to apply to.*

- [ ] **Step 1.1:** Basic Scraper Implementation.
    - Implement `scrapers/hunter.py` using `python-jobspy`.
    - Config: Search "AI Engineer" on LinkedIn/Indeed/Glassdoor.
- [ ] **Step 1.2:** Filtering Logic.
    - Filter results to keep **ONLY** `greenhouse.io`, `lever.co`, and `ashbyhq.com` links.
    - Discard "Easy Apply" (LinkedIn native) and "Workday" (Login walls) for MVP.
- [ ] **Step 1.3:** Deduplication.
    - Create a simple check against `jobs.csv` to ensure we don't fetch already applied jobs.

---

## 🧠 Phase 2: The Brain (Memory & RAG)
*Goal: Stop the agent from hallucinating or asking repetitive questions.*

- [ ] **Step 2.1:** Knowledge Base Setup.
    - Create `memory/brain.py`.
    - Implement `train_brain()`: Load `profile_stories.txt`, split text, and save to ChromaDB.
    - **Checkpoint:** Run script and verify `chroma_db` folder is created.
- [ ] **Step 2.2:** Groq Integration (Text).
    - Implement `ask_brain(query)` using `ChatGroq` (Llama 3.3 70B).
    - Logic: Retrieve context from ChromaDB -> Send to Groq -> Return clean string answer.
- [ ] **Step 2.3:** Static Data Handler.
    - Create `static_profile.json` handler for simple fields (First Name, Email, Phone) to save LLM tokens.

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