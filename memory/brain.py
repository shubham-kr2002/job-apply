"""
AI Auto-Applier Agent - Phase 2: Memory Layer
RAG-based Question Answering System for Job Applications

Implements:
- FR-3.1: Profile ingestion (static JSON + unstructured stories)
- FR-3.2: Intelligent reasoning with Groq LLM
- UI Requirement: Structured JSON responses with confidence scores
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# Pydantic models for type safety (UI-ready JSON responses)
class BrainResponse(BaseModel):
    """
    Structured response for job application questions.
    Designed for Next.js dashboard integration.
    """
    answer: str = Field(description="The actual text to type into the form field")
    confidence: float = Field(
        ge=0.0, 
        le=1.0, 
        description="Confidence score (0.0-1.0) for manual override support"
    )
    reasoning: str = Field(description="Source of the answer (for transparency)")
    source_type: str = Field(description="'static_profile', 'vector_search', or 'llm_generated'")


class StaticProfile(BaseModel):
    """Schema for static_profile.json"""
    name: str
    email: str
    phone: str
    linkedin: str
    github: Optional[str] = None
    location: str
    current_title: str
    years_of_experience: int
    skills: List[str]
    education: List[dict]
    certifications: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    availability: Optional[str] = None
    work_authorization: Optional[str] = None
    preferred_locations: Optional[List[str]] = []
    salary_expectation: Optional[str] = None


class BrainAgent:
    """
    RAG-powered intelligent agent for job application form filling.
    
    Architecture:
    1. Static Profile Lookup (for exact matches)
    2. Vector Search (for narrative questions)
    3. Groq LLM (for reasoning and synthesis)
    """
    
    def __init__(
        self, 
        groq_api_key: Optional[str] = None,
        data_dir: str = "data",
        chroma_dir: str = "./chroma_db"
    ):
        """
        Initialize BrainAgent with Groq LLM and ChromaDB.
        
        Args:
            groq_api_key: Groq API key (or set GROQ_API_KEY env var)
            data_dir: Directory containing profile data
            chroma_dir: ChromaDB persistence directory
        """
        self.data_dir = Path(data_dir)
        self.chroma_dir = Path(chroma_dir)
        
        # Load Groq API key
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not found. Set it via environment or parameter.")
        
        # Initialize Groq LLM (Llama 3.3 70B)
        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.3,  # Lower temperature for consistent answers
            max_tokens=500
        )
        logger.info("Groq LLM initialized: llama-3.3-70b-versatile")
        
        # Initialize embeddings (HuggingFace - fast and local)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("HuggingFace embeddings initialized: all-MiniLM-L6-v2")
        
        # Load static profile
        self.static_profile = self._load_static_profile()
        
        # Initialize ChromaDB
        self.vectorstore = None
        if self.chroma_dir.exists():
            try:
                self.vectorstore = Chroma(
                    persist_directory=str(self.chroma_dir),
                    embedding_function=self.embeddings
                )
                logger.info(f"ChromaDB loaded from {self.chroma_dir}")
            except Exception as e:
                logger.warning(f"Could not load existing ChromaDB: {e}")
    
    def _load_static_profile(self) -> Optional[StaticProfile]:
        """
        Load static_profile.json for exact field lookups.
        Implements FR-3.1 (Ingestion - Static Data)
        """
        profile_path = self.data_dir / "static_profile.json"
        if not profile_path.exists():
            logger.warning(f"static_profile.json not found at {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            profile = StaticProfile(**profile_data)
            logger.info(f"Loaded static profile: {profile.name}")
            return profile
        except Exception as e:
            logger.error(f"Error loading static profile: {e}")
            return None
    
    def train_brain(self, stories_file: str = "profile_stories.txt") -> bool:
        """
        Ingest profile_stories.txt into ChromaDB vector store.
        Implements FR-3.1 (Ingestion - Unstructured Stories)
        
        Args:
            stories_file: Filename in data_dir containing narrative bio
        
        Returns:
            Success status
        """
        stories_path = self.data_dir / stories_file
        
        if not stories_path.exists():
            logger.error(f"Stories file not found: {stories_path}")
            return False
        
        try:
            # Read stories file
            with open(stories_path, 'r', encoding='utf-8') as f:
                stories_text = f.read()
            
            logger.info(f"Loaded {len(stories_text)} characters from {stories_file}")
            
            # Chunk the text for better retrieval
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            chunks = text_splitter.split_text(stories_text)
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Create documents with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": stories_file,
                        "chunk_id": i,
                        "type": "profile_story"
                    }
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # Create or update ChromaDB
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(self.chroma_dir)
            )
            
            logger.info(f"✓ Brain training complete. {len(documents)} chunks stored in ChromaDB.")
            return True
            
        except Exception as e:
            logger.error(f"Error during brain training: {e}")
            return False
    
    def _check_static_profile(self, question: str) -> Optional[BrainResponse]:
        """
        Check if question can be answered from static_profile.json.
        Implements exact field matching for standard form fields.
        
        Args:
            question: The form field question
        
        Returns:
            BrainResponse if match found, None otherwise
        """
        if not self.static_profile:
            return None
        
        question_lower = question.lower()
        
        # Mapping of common question patterns to profile fields
        field_mappings = {
            "name": (["name", "full name", "your name"], self.static_profile.name),
            "email": (["email", "email address", "e-mail"], self.static_profile.email),
            "phone": (["phone", "phone number", "mobile", "contact number"], self.static_profile.phone),
            "linkedin": (["linkedin", "linkedin profile", "linkedin url"], self.static_profile.linkedin),
            "github": (["github", "github profile", "github url"], self.static_profile.github or "N/A"),
            "location": (["location", "city", "where are you based", "current location"], self.static_profile.location),
            "experience": (["years of experience", "how many years", "experience"], str(self.static_profile.years_of_experience)),
            "current_title": (["current role", "current position", "job title"], self.static_profile.current_title),
            "availability": (["availability", "notice period", "when can you join"], self.static_profile.availability or "Immediately"),
            "work_authorization": (["work authorization", "visa status", "work permit"], self.static_profile.work_authorization or "Authorized to work"),
            "salary": (["salary", "expected salary", "compensation", "ctc"], self.static_profile.salary_expectation or "As per market standards"),
        }
        
        # Check for matches
        for field_name, (patterns, value) in field_mappings.items():
            if any(pattern in question_lower for pattern in patterns):
                return BrainResponse(
                    answer=str(value),
                    confidence=0.95,  # High confidence for exact matches
                    reasoning=f"Direct match from static_profile.json ({field_name})",
                    source_type="static_profile"
                )
        
        # Check skills
        if "skill" in question_lower or "technologies" in question_lower:
            skills_str = ", ".join(self.static_profile.skills)
            return BrainResponse(
                answer=skills_str,
                confidence=0.95,
                reasoning="Skills list from static_profile.json",
                source_type="static_profile"
            )
        
        return None
    
    def _retrieve_context(self, question: str, k: int = 3) -> str:
        """
        Retrieve relevant context from ChromaDB using similarity search.
        
        Args:
            question: Query text
            k: Number of relevant chunks to retrieve
        
        Returns:
            Concatenated context string
        """
        if not self.vectorstore:
            logger.warning("VectorStore not initialized. Run train_brain() first.")
            return ""
        
        try:
            docs = self.vectorstore.similarity_search(question, k=k)
            context = "\n\n".join([doc.page_content for doc in docs])
            logger.info(f"Retrieved {len(docs)} relevant chunks from ChromaDB")
            return context
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return ""
    
    def ask_brain(self, question: str, job_context: str = "") -> BrainResponse:
        """
        Answer a job application question using RAG pipeline.
        Implements FR-3.2 (Reasoning)
        
        Pipeline:
        1. Check static_profile.json for exact matches
        2. Perform similarity search in ChromaDB
        3. Use Groq LLM to synthesize answer
        4. Return structured JSON response
        
        Args:
            question: The form field question (e.g., "Why do you want this job?")
            job_context: Optional context about the job (company, role)
        
        Returns:
            BrainResponse with answer, confidence, and reasoning
        """
        logger.info(f"Question received: {question}")
        
        # Step 1: Check static profile first
        static_answer = self._check_static_profile(question)
        if static_answer:
            logger.info("✓ Answered from static_profile.json")
            return static_answer
        
        # Step 2: Retrieve context from vector store
        retrieved_context = self._retrieve_context(question, k=3)
        
        if not retrieved_context:
            logger.warning("No relevant context found in vector store")
            return BrainResponse(
                answer="Please provide this information manually.",
                confidence=0.0,
                reasoning="No relevant context available",
                source_type="fallback"
            )
        
        # Step 3: Generate answer using Groq LLM
        try:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", """You are an AI assistant helping fill out job application forms.

Your task: Answer the question based ONLY on the provided context from the candidate's profile.

CRITICAL RULES:
1. Keep answers concise (2-3 sentences max for short-answer fields)
2. Use first-person perspective ("I have...", "My experience...")
3. If the context doesn't contain relevant information, say "Information not available in profile"
4. Do NOT make up facts or experiences not in the context
5. Tailor the answer slightly to the job context if provided

Context from candidate's profile:
{context}

Job Context (if available):
{job_context}
"""),
                ("user", "Question: {question}\n\nProvide a concise, relevant answer.")
            ])
            
            prompt = prompt_template.format_messages(
                context=retrieved_context,
                job_context=job_context or "Not provided",
                question=question
            )
            
            response = self.llm.invoke(prompt)
            answer_text = response.content.strip()
            
            # Calculate confidence based on context relevance
            # Simple heuristic: longer retrieved context = higher confidence
            confidence = min(0.85, 0.60 + (len(retrieved_context) / 2000))
            
            logger.info("✓ Answer generated using Groq LLM")
            
            return BrainResponse(
                answer=answer_text,
                confidence=round(confidence, 2),
                reasoning="Generated from profile stories using vector search + Groq LLM",
                source_type="llm_generated"
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return BrainResponse(
                answer="Error generating response. Please answer manually.",
                confidence=0.0,
                reasoning=f"LLM Error: {str(e)}",
                source_type="error"
            )
    
    def get_profile_summary(self) -> dict:
        """
        Get a summary of loaded profile data.
        Useful for debugging and dashboard display.
        
        Returns:
            Dictionary with profile stats
        """
        summary = {
            "static_profile_loaded": self.static_profile is not None,
            "vectorstore_ready": self.vectorstore is not None,
            "groq_configured": self.groq_api_key is not None
        }
        
        if self.static_profile:
            summary["candidate_name"] = self.static_profile.name
            summary["skills_count"] = len(self.static_profile.skills)
        
        if self.vectorstore:
            try:
                # Get collection stats
                collection = self.vectorstore._collection
                summary["vector_chunks"] = collection.count()
            except:
                summary["vector_chunks"] = "Unknown"
        
        return summary


# Example usage and testing
if __name__ == "__main__":
    """
    Standalone test script for BrainAgent
    """
    print("="*60)
    print("AI Auto-Applier Agent - Phase 2: Memory Layer Test")
    print("="*60)
    
    # Initialize agent
    brain = BrainAgent()
    
    # Train the brain (first time only)
    print("\n[1/3] Training brain with profile_stories.txt...")
    success = brain.train_brain()
    
    if not success:
        print("❌ Brain training failed. Check logs.")
        exit(1)
    
    print("✓ Brain training complete")
    
    # Test queries
    print("\n[2/3] Testing static profile queries...")
    test_questions = [
        "What is your name?",
        "What is your email address?",
        "How many years of experience do you have?",
        "What are your technical skills?",
    ]
    
    for q in test_questions:
        response = brain.ask_brain(q)
        print(f"\nQ: {q}")
        print(f"A: {response.answer}")
        print(f"Confidence: {response.confidence} | Source: {response.source_type}")
    
    # Test narrative questions
    print("\n[3/3] Testing narrative questions (RAG)...")
    narrative_questions = [
        "Tell me about a challenging project you worked on.",
        "What is your biggest weakness?",
        "Why are you interested in AI/ML?",
    ]
    
    for q in narrative_questions:
        response = brain.ask_brain(
            q, 
            job_context="Senior AI Engineer role at a startup building RAG systems"
        )
        print(f"\nQ: {q}")
        print(f"A: {response.answer[:200]}...")  # Truncate long answers
        print(f"Confidence: {response.confidence} | Source: {response.source_type}")
    
    # Show profile summary
    print("\n" + "="*60)
    print("Profile Summary:")
    print(json.dumps(brain.get_profile_summary(), indent=2))
    print("="*60)
