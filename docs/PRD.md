# Product Requirements Document (PRD)
**Project:** AI Auto-Applier Agent (Groq Edition)
**Version:** 2.0 (Groq Optimization)
**Date:** January 6, 2026
**Owner:** Shubham (Vibe Coder)

---

## 1. Executive Summary
The **AI Auto-Applier Agent** is a high-performance, autonomous system designed to eliminate manual data entry in job applications. By leveraging **Groq's LPU Inference Engine**, the system achieves near-instantaneous reasoning (<0.5s) to analyze complex web forms, map semantic fields, and submit applications. It features a "Human-in-the-Loop" memory system that learns from user inputs, ensuring it adapts to new questions without constant retraining.

## 2. Problem Statement
* **Pain Point:** Applying for jobs involves repetitive form filling and answering the same "Why Us?" questions across hundreds of portals.
* **Limitation of Current Tools:** Selenium scripts are brittle and break on UI changes. Standard GPT-4o agents are too slow and expensive for high-volume iteration.
* **Solution:** A Vision/LLM-based agent using **Llama 3 on Groq** for sub-second decision making, robust against DOM changes and Shadow DOMs.

## 3. Goals & Success Metrics
* **Efficiency:** Reduce application time to **<30 seconds per job** (Machine time).
* **Accuracy:** >90% success rate in mapping form fields correctly on Greenhouse/Lever.
* **Latency:** Core reasoning step (HTML -> Selectors) must complete in **<1 second** using Groq.
* **User Experience:** The agent must never ask the same question twice (0% Redundancy).

---

## 4. User Stories & Functional Requirements

### 4.1. Job Discovery (The Hunter)
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-1.1** | System must aggregate jobs from LinkedIn, Indeed, Glassdoor using `jobspy`. | P0 |
| **FR-1.2** | System must strictly filter for supported ATS domains (`greenhouse.io`, `lever.co`, `ashbyhq.com`). | P0 |
| **FR-1.3** | System must deduplicate jobs against a historical `jobs.csv` log. | P1 |

### 4.2. Intelligent Form Filling (The Vision)
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-2.1** | System must inject a JavaScript "Flattener" to expose Shadow DOM inputs to the LLM. | P0 |
| **FR-2.2** | System must use **Llama-3.3-70b (via Groq)** to map HTML elements to user profile keys. | P0 |
| **FR-2.3** | System must handle standard inputs (Text, Checkbox, Radio) and File Uploads. | P0 |
| **FR-2.4** | System must implement **Stealth Mode** (Randomized delays, Bezier mouse curves) to avoid bot detection. | P1 |

### 4.3. Contextual Memory (The Brain)
| ID | Requirement | Priority |
| :--- | :--- | :--- |
| **FR-3.1** | System must index user's text biography (`profile_stories.txt`) into **ChromaDB**. | P0 |
| **FR-3.2** | System must use RAG (Retrieval Augmented Generation) to answer open-ended questions (e.g., "Describe a challenge..."). | P0 |
| **FR-3.3** | **Interrupt Protocol:** If confidence is low or data is missing, the system must PAUSE, prompt the user via CLI, save the new answer, and RESUME. | P1 |

---

## 5. Technical Requirements

### 5.1. Tech Stack
* **Inference:** Groq API (Llama 3.3 70B Versatile).
* **Browser:** Playwright (Python Async).
* **Database:** ChromaDB (Local Vector Store).
* **Language:** Python 3.10+.

### 5.2. Performance Constraints
* **Token Optimization:** HTML sent to Groq must be stripped of `<script>`, `<style>`, `<svg>` to stay within TPM (Tokens Per Minute) limits.
* **Rate Limiting:** Must handle Groq `429 Too Many Requests` with exponential backoff.

### 5.3. Security & Stealth
* **Data:** API Keys stored in `.env`. Personal data stored locally (no cloud upload of resume).
* **Anti-Bot:** User Agent rotation and `ghost-cursor` implementation required.

---

## 6. Data Requirements

### 6.1. User Profile Structure (`static_profile.json`)
```json
{
  "first_name": "Shubham",
  "last_name": "Kumar",
  "email": "shubham@example.com",
  "linkedin": "[https://linkedin.com/in/](https://linkedin.com/in/)...",
  "portfolio": "https://...",
  "resume_path": "./data/resume.pdf"
}