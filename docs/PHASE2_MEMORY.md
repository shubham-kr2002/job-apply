# Phase 2: Memory Layer - Setup Guide

## 🧠 Overview

The Memory Layer implements a RAG (Retrieval Augmented Generation) system that intelligently answers job application questions using:
- **Static Profile** (exact field matching)
- **Vector Search** (ChromaDB with semantic similarity)
- **LLM Reasoning** (Groq's Llama 3.3 70B)

## 🚀 Quick Start

### 1. Install Phase 2 Dependencies

```bash
# Ensure venv is activated
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install new dependencies
pip install -r requirements.txt
```

### 2. Get Groq API Key

1. Visit [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (free tier available)
3. Create a new API key
4. Copy the key

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and add your Groq API key
# GROQ_API_KEY=gsk_your_actual_key_here
```

### 4. Test the Brain Agent

```bash
# Run standalone test
python memory/brain.py
```

Expected output:
```
[1/3] Training brain with profile_stories.txt...
✓ Brain training complete

[2/3] Testing static profile queries...
Q: What is your name?
A: Shubham Kumar
Confidence: 0.95 | Source: static_profile

[3/3] Testing narrative questions (RAG)...
Q: Tell me about a challenging project you worked on.
A: In my role as Senior AI Engineer at TechCorp, I led the development...
Confidence: 0.82 | Source: llm_generated
```

---

## 📂 Data Files

### `data/static_profile.json`

**Purpose:** Structured data for exact field matching (name, email, skills, etc.)

**When to Edit:**
- Update your personal information
- Add new skills or certifications
- Change contact details

**Example Fields:**
```json
{
  "name": "Your Name",
  "email": "your.email@example.com",
  "phone": "+91-1234567890",
  "skills": ["Python", "LangChain", "RAG"],
  "years_of_experience": 5
}
```

### `data/profile_stories.txt`

**Purpose:** Unstructured narrative content for behavioral/essay questions

**Structure:**
1. **Challenging Projects** - Technical achievements and problem-solving
2. **Leadership & Collaboration** - Team work and mentorship
3. **Weaknesses & Growth** - Self-awareness and improvement
4. **Passion & Motivation** - Why you're interested in the field

**Tips for Writing:**
- Use specific examples with metrics ("reduced latency by 40%")
- Include technologies and methodologies
- Write in first person
- Keep paragraphs focused on one theme

---

## 🎯 How It Works

### Three-Tier Answer System

```mermaid
Question → Static Profile Check → Vector Search → LLM Generation → JSON Response
           ↓ (if exact match)    ↓ (if narrative)  ↓ (synthesis)
         [name, email, etc]   [stories context]  [reasoned answer]
```

### 1. **Static Profile Lookup** (Confidence: 0.95)
- Fast exact matching for standard fields
- Questions like: "What is your email?" → `static_profile.json`

### 2. **Vector Search** (Confidence: 0.60-0.85)
- Semantic similarity search in ChromaDB
- Questions like: "Tell me about a challenge" → `profile_stories.txt` chunks

### 3. **LLM Generation** (Confidence: varies)
- Groq synthesizes answer from retrieved context
- Ensures answers are relevant and concise

---

## 🔧 API Usage (For Next.js Integration)

### Python Usage

```python
from memory.brain import BrainAgent

# Initialize agent
brain = BrainAgent(groq_api_key="your_key")

# Train brain (one-time, or when profile updates)
brain.train_brain()

# Ask questions
response = brain.ask_brain(
    question="Why do you want this job?",
    job_context="Senior AI Engineer at TechCorp, working on RAG systems"
)

# Response is a Pydantic model (JSON-serializable)
print(response.model_dump_json(indent=2))
```

### Response Format (JSON)

```json
{
  "answer": "I'm passionate about building RAG systems...",
  "confidence": 0.82,
  "reasoning": "Generated from profile stories using vector search + Groq LLM",
  "source_type": "llm_generated"
}
```

**Fields:**
- `answer` (str): The actual text to fill in the form
- `confidence` (float): 0.0-1.0, for manual override UI
- `reasoning` (str): Explanation of where answer came from
- `source_type` (str): `static_profile`, `llm_generated`, `error`, or `fallback`

---

## 🎨 Integration with Next.js Dashboard

### Confidence-Based UI

```typescript
// Example Next.js component logic
const response = await fetch('/api/ask-brain', {
  method: 'POST',
  body: JSON.stringify({ question: "Why this job?" })
});

const data = await response.json();

// Show confidence indicator
if (data.confidence < 0.5) {
  // Show warning: "Low confidence - please review"
  // Enable manual edit mode by default
}

if (data.confidence >= 0.95) {
  // Auto-fill with high confidence
  // Green checkmark indicator
}
```

### Manual Override Support

The confidence score enables:
- **Auto-fill** for high confidence (>0.9)
- **Suggest with review** for medium (0.5-0.9)
- **Manual entry** for low (<0.5)

---

## 🛠️ Customization

### Change LLM Model

Edit `memory/brain.py`:

```python
self.llm = ChatGroq(
    groq_api_key=self.groq_api_key,
    model_name="mixtral-8x7b-32768",  # Alternative model
    temperature=0.5,  # Higher = more creative
    max_tokens=1000   # Longer answers
)
```

### Adjust Vector Search

```python
# In _retrieve_context method
docs = self.vectorstore.similarity_search(question, k=5)  # Get more chunks
```

### Custom Question Mappings

Add to `_check_static_profile()` in `brain.py`:

```python
field_mappings = {
    "custom_field": (["pattern1", "pattern2"], self.static_profile.custom_value),
    # ...
}
```

---

## 🐛 Troubleshooting

### "GROQ_API_KEY not found"

**Solution:**
```bash
# Set environment variable
# Windows PowerShell:
$env:GROQ_API_KEY="gsk_your_key"

# Linux/macOS:
export GROQ_API_KEY="gsk_your_key"

# Or edit .env file
```

### ChromaDB Import Error

**Solution:**
```bash
pip install --upgrade chromadb langchain-chroma
```

### HuggingFace Model Download Slow

**First run only** - downloads `all-MiniLM-L6-v2` model (~90MB)
- Subsequent runs use cached model
- No internet needed after first download

### "No relevant context found"

**Causes:**
1. `train_brain()` not called yet
2. `profile_stories.txt` is empty or missing

**Solution:**
```python
brain = BrainAgent()
brain.train_brain()  # Run this first!
```

---

## 📊 Performance Metrics

| Component | Latency | Notes |
|-----------|---------|-------|
| Static Profile Lookup | <10ms | Instant JSON lookup |
| Vector Search | 50-100ms | Local ChromaDB |
| Groq LLM (Llama 3.3) | 1-3s | Fast inference |
| **Total Pipeline** | **1-3s** | Real-time responses |

---

## 🔐 Security Best Practices

1. **Never commit `.env`** to git (already in `.gitignore`)
2. **Rotate API keys** periodically
3. **Use environment variables** in production
4. **Sanitize user inputs** before LLM calls
5. **Rate limit API calls** in production

---

## 📈 Next Steps (Phase 3)

- [ ] API endpoint for Next.js (`/api/brain`)
- [ ] Batch question answering
- [ ] Resume/CV parsing and ingestion
- [ ] Multi-profile support (different resumes)
- [ ] Fine-tuned embeddings for job domain

---

## 🧪 Testing Commands

```bash
# Test static profile answers
python -c "from memory.brain import BrainAgent; b = BrainAgent(); print(b.ask_brain('What is your email?').model_dump_json())"

# Test narrative question
python memory/brain.py

# Check profile summary
python -c "from memory.brain import BrainAgent; import json; b = BrainAgent(); print(json.dumps(b.get_profile_summary(), indent=2))"
```

---

## 📚 Architecture Reference

```
BrainAgent
├── Groq LLM (Llama 3.3 70B)
│   └── Temperature: 0.3 (consistent answers)
├── ChromaDB (Vector Store)
│   ├── Embeddings: all-MiniLM-L6-v2
│   ├── Chunks: 500 chars, 50 overlap
│   └── Persistence: ./chroma_db/
├── Static Profile (JSON)
│   └── Exact field matching
└── Response Model (Pydantic)
    ├── answer: str
    ├── confidence: float
    ├── reasoning: str
    └── source_type: str
```

---

**Built for Next.js Dashboard Integration** | **JSON-First API Design** | **Production-Ready RAG System**
