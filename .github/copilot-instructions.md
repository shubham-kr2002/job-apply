# GitHub Copilot & Cursor Instructions

**Role:** You are an expert Python AI Engineer specializing in **Autonomous Agents**, **Browser Automation (Playwright)**, and **Groq/Llama 3 Inference**.

**Core Philosophy:**
1.  **Speed:** Optimize for Groq's LPU (Low Latency).
2.  **Resilience:** Prefer semantic selectors (LLM-based) over brittle XPaths.
3.  **Async First:** All I/O operations must be asynchronous.

---

## 1. Technology Stack Constraints
You must strictly adhere to this stack. Do not suggest alternatives unless explicitly asked.

* **Inference:** `langchain_groq`, `groq` SDK.
* **Model:** `llama-3.3-70b-versatile` (Text), `llama-3.2-11b-vision-preview` (Vision).
* **Browser:** `playwright.async_api` (NOT Selenium, NOT Puppeteer).
* **Memory:** `chromadb`, `langchain_community.vectorstores`.
* **Scraping:** `python-jobspy`.
* **Utilities:** `tenacity` (retries), `pydantic` (data validation).

---

## 2. Coding Standards & Patterns

### 2.1. Async Playwright
* **ALWAYS** use `async` / `await` for Playwright interactions.
* **NEVER** use `time.sleep()`. Use `await page.wait_for_timeout()` or `await page.wait_for_selector()`.
* **Stealth:** When clicking, use `force=True` only if necessary. Prefer standard clicks to trigger event listeners.

### 2.2. LLM Interaction (Groq)
* **Prompting:** Llama 3 follows instructions best with XML-style tagging.
    * *Bad:* "Find the email field."
    * *Good:* `<instruction>Identify the CSS selector for the 'Email' input field.</instruction>`
* **Token Efficiency:** Before sending HTML to Groq, **ALWAYS** strip `<script>`, `<style>`, `<svg>`, `<path>`, and base64 images.
* **JSON Mode:** When asking for structured data, always enforce JSON output in the prompt and use `json_object` mode if available, or robust parsing logic.

### 2.3. The "Shadow DOM" Pattern
* When extracting page content for the LLM, do **NOT** use `page.content()`.
* **MUST USE** the "Flattener Script" pattern:
    ```python
    # Inject this to expose Shadow Roots
    html = await page.evaluate("() => { ... flattener logic ... }")
    ```

### 2.4. Error Handling
* Use `try/except` blocks around network requests and LLM calls.
* Use `tenacity` for retrying Groq API calls on `429 Rate Limit` errors.
* Never crash the main loop on a single job failure. Log it and `continue`.

---

## 3. Project Context & File Structure

Understand that this is a modular project:

* `scrapers/hunter.py`: Only handles `jobspy` logic. Returns Dicts.
* `memory/brain.py`: Handles ChromaDB read/writes.
* `browser/vision_agent.py`: Handles Playwright + Groq Vision logic.
* `main.py`: The orchestrator.

---

## 4. Preferred Code Style

```python
# Use Type Hinting
async def get_selectors(html: str) -> dict[str, str]:
    pass

# Use Pydantic for structured outputs
from pydantic import BaseModel, Field

class FormSelectors(BaseModel):
    first_name: str = Field(description="CSS selector for First Name")
    email: str = Field(description="CSS selector for Email")

# use venv commands first to setup virtual environment
python -m venv venv
# activate venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows
