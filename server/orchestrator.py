"""
AI Auto-Applier Agent - Phase 4: Job Orchestrator

This module coordinates the entire job application pipeline:
- Hunter: Discovers job URLs from multiple platforms
- Brain: Answers application questions using RAG
- Vision: Automates browser interactions

Key Features:
- Async execution with pause/resume for human-in-the-loop
- Real-time event broadcasting via WebSocket callbacks
- Graceful stop mechanism
- State machine for tracking application progress

The "Pause/Resume" Logic:
-------------------------
When the Brain returns low confidence (<0.6), we need human input:

1. The orchestrator creates an `asyncio.Event()` called `_human_input_event`
2. It emits a `request_input` WebSocket message to the frontend
3. It calls `await _human_input_event.wait()` - this BLOCKS the coroutine
4. The coroutine is suspended, but the event loop continues (other tasks run)
5. When the user submits an answer via `POST /submit_override`:
   - The API stores the answer in `_pending_input`
   - Calls `_human_input_event.set()` to wake up the orchestrator
6. The orchestrator resumes, reads `_pending_input`, and continues filling

This pattern allows true async pause/resume without blocking the entire server.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ApplicationState(str, Enum):
    """State machine for job application status."""
    IDLE = "idle"
    STARTING = "starting"
    FETCHING_JOBS = "fetching_jobs"
    NAVIGATING = "navigating"
    SCANNING = "scanning"
    ANSWERING = "answering"
    WAITING_INPUT = "waiting_input"  # Human-in-the-loop pause
    FILLING = "filling"
    SUBMITTING = "submitting"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class JobApplication:
    """Tracks state for a single job application."""
    job_id: str
    company: str
    title: str
    url: str
    ats_provider: str
    status: str = "pending"
    fields_detected: int = 0
    fields_filled: int = 0
    questions_asked: int = 0
    questions_manual: int = 0  # Required human input
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    screenshot_b64: Optional[str] = None


@dataclass
class OrchestratorStats:
    """Runtime statistics for the orchestrator."""
    jobs_processed: int = 0
    jobs_successful: int = 0
    jobs_failed: int = 0
    questions_answered: int = 0
    questions_manual_override: int = 0
    total_runtime_seconds: float = 0.0
    current_job: Optional[JobApplication] = None


class JobOrchestrator:
    """
    Coordinates Hunter, Brain, and Vision for automated job applications.
    
    This is the central nervous system of the AI Auto-Applier:
    - Fetches jobs from Hunter (scraped URLs)
    - Uses Brain to answer application questions
    - Controls Vision (browser) to fill forms
    - Pauses for human input when confidence is low
    
    Usage:
        orchestrator = JobOrchestrator(
            on_event=websocket_broadcast_function,
            on_screenshot=screenshot_handler
        )
        await orchestrator.start()
        # Later...
        await orchestrator.stop()
    """
    
    # Minimum confidence threshold for auto-fill
    CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(
        self,
        on_event: Optional[Callable[[str, Any], None]] = None,
        on_screenshot: Optional[Callable[[str], None]] = None,
        headless: bool = False,
        dry_run: bool = False  # If True, don't actually submit forms
    ):
        """
        Initialize the Job Orchestrator.
        
        Args:
            on_event: Callback for WebSocket events (type, data)
            on_screenshot: Callback for screenshot updates
            headless: Run browser in headless mode
            dry_run: If True, skip final form submission
        """
        self.on_event = on_event
        self.on_screenshot = on_screenshot
        self.headless = headless
        self.dry_run = dry_run
        
        # State
        self._state = ApplicationState.IDLE
        self._stats = OrchestratorStats()
        self._is_running = False
        self._stop_requested = False
        
        # Human-in-the-loop synchronization
        self._human_input_event = asyncio.Event()
        self._pending_input: Optional[str] = None
        self._pending_question: Optional[str] = None
        
        # Job queue
        self._job_queue: asyncio.Queue = asyncio.Queue()
        self._current_job: Optional[JobApplication] = None
        
        # Background task reference
        self._run_task: Optional[asyncio.Task] = None
        
        # Module instances (lazy loaded)
        self._hunter = None
        self._brain = None
        self._vision = None
        
        logger.info("JobOrchestrator initialized (headless=%s, dry_run=%s)", headless, dry_run)
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def state(self) -> ApplicationState:
        """Current state of the orchestrator."""
        return self._state
    
    @property
    def stats(self) -> OrchestratorStats:
        """Runtime statistics."""
        return self._stats
    
    @property
    def is_running(self) -> bool:
        """Check if orchestrator is currently running."""
        return self._is_running
    
    @property
    def is_waiting_input(self) -> bool:
        """Check if waiting for human input."""
        return self._state == ApplicationState.WAITING_INPUT
    
    # =========================================================================
    # EVENT EMISSION
    # =========================================================================
    
    def _emit(self, event_type: str, data: Any) -> None:
        """Emit an event to the WebSocket callback."""
        if self.on_event:
            try:
                self.on_event(event_type, data)
            except Exception as e:
                logger.warning("Event emission failed: %s", str(e))
        
        # Also log important events
        if event_type == "log":
            logger.info("[EVENT] %s", data)
        elif event_type == "state":
            logger.info("[STATE] %s", data)
        elif event_type == "error":
            logger.error("[ERROR] %s", data)
    
    def _emit_log(self, message: str) -> None:
        """Emit a log message."""
        self._emit("log", message)
    
    def _emit_state(self, state: ApplicationState) -> None:
        """Update and emit state change."""
        self._state = state
        self._emit("state", {
            "state": state.value,
            "timestamp": datetime.now().isoformat()
        })
    
    def _emit_screenshot(self, b64_data: str) -> None:
        """Emit screenshot to frontend."""
        self._emit("screenshot", b64_data)
        if self.on_screenshot:
            self.on_screenshot(b64_data)
    
    def _emit_request_input(self, question: str, context: str, field_info: Dict) -> None:
        """Request human input from frontend."""
        self._pending_question = question
        self._emit("request_input", {
            "question": question,
            "context": context,
            "field": field_info,
            "timestamp": datetime.now().isoformat()
        })
    
    def _emit_stats(self) -> None:
        """Emit current statistics."""
        self._emit("stats", {
            "jobs_processed": self._stats.jobs_processed,
            "jobs_successful": self._stats.jobs_successful,
            "jobs_failed": self._stats.jobs_failed,
            "questions_answered": self._stats.questions_answered,
            "questions_manual": self._stats.questions_manual_override,
            "current_job": {
                "company": self._current_job.company if self._current_job else None,
                "title": self._current_job.title if self._current_job else None,
                "status": self._current_job.status if self._current_job else None
            } if self._current_job else None
        })
    
    # =========================================================================
    # LIFECYCLE MANAGEMENT
    # =========================================================================
    
    async def start(self) -> None:
        """
        Start the orchestrator in a background task.
        
        This is non-blocking - it spawns the run loop as an async task
        and returns immediately.
        """
        if self._is_running:
            logger.warning("Orchestrator already running")
            return
        
        self._is_running = True
        self._stop_requested = False
        self._emit_state(ApplicationState.STARTING)
        
        # Initialize modules
        await self._init_modules()
        
        # Start the main loop as a background task
        self._run_task = asyncio.create_task(self._run_loop())
        
        self._emit_log("🚀 Orchestrator started")
    
    async def stop(self) -> None:
        """
        Gracefully stop the orchestrator.
        
        Sets stop flag and wakes up any waiting events.
        """
        if not self._is_running:
            return
        
        self._emit_log("🛑 Stop requested, finishing current job...")
        self._stop_requested = True
        
        # Wake up human input wait if blocked
        self._human_input_event.set()
        
        # Wait for run task to complete
        if self._run_task:
            try:
                await asyncio.wait_for(self._run_task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Run task did not complete in time, cancelling")
                self._run_task.cancel()
        
        # Cleanup
        await self._cleanup_modules()
        
        self._is_running = False
        self._emit_state(ApplicationState.STOPPED)
        self._emit_log("✓ Orchestrator stopped")
    
    async def submit_override(self, answer: str) -> bool:
        """
        Submit human input to resolve a pending question.
        
        Called from the API when user provides an answer.
        
        Args:
            answer: The human-provided answer
        
        Returns:
            True if input was accepted, False if not waiting
        """
        if not self.is_waiting_input:
            logger.warning("submit_override called but not waiting for input")
            return False
        
        self._pending_input = answer
        self._stats.questions_manual_override += 1
        
        # Wake up the waiting coroutine
        self._human_input_event.set()
        
        self._emit_log(f"✓ Received human input: {answer[:50]}...")
        return True
    
    # =========================================================================
    # MODULE INITIALIZATION
    # =========================================================================
    
    async def _init_modules(self) -> None:
        """Initialize Hunter, Brain, and Vision modules."""
        self._emit_log("Initializing modules...")
        
        try:
            # Import modules (lazy to avoid circular imports)
            from scrapers.hunter import JobHunter
            from memory.brain import BrainAgent
            from browser.vision_agent import VisionAgent
            
            # Initialize Hunter (sync)
            self._hunter = JobHunter()
            self._emit_log("✓ Hunter initialized")
            
            # Initialize Brain (sync, loads embeddings)
            self._brain = BrainAgent()
            self._emit_log("✓ Brain initialized")
            
            # Initialize Vision with screenshot callback
            self._vision = VisionAgent(
                headless=self.headless,
                screenshot_callback=self._emit_screenshot
            )
            await self._vision.start_session()
            self._emit_log("✓ Vision initialized")
            
        except Exception as e:
            self._emit_state(ApplicationState.ERROR)
            self._emit("error", f"Module initialization failed: {str(e)}")
            raise
    
    async def _cleanup_modules(self) -> None:
        """Cleanup module resources."""
        if self._vision:
            await self._vision.close()
            self._vision = None
        
        self._hunter = None
        self._brain = None
    
    # =========================================================================
    # MAIN RUN LOOP
    # =========================================================================
    
    async def _run_loop(self) -> None:
        """
        Main orchestration loop.
        
        This runs as a background task and processes jobs sequentially.
        """
        start_time = time.time()
        
        try:
            # Step 1: Fetch jobs
            self._emit_state(ApplicationState.FETCHING_JOBS)
            jobs = await self._fetch_jobs()
            
            if not jobs:
                self._emit_log("⚠ No jobs found matching criteria")
                return
            
            self._emit_log(f"📋 Found {len(jobs)} jobs to process")
            
            # Step 2: Process each job
            for job_data in jobs:
                if self._stop_requested:
                    self._emit_log("Stop requested, exiting loop")
                    break
                
                try:
                    await self._process_job(job_data)
                    self._stats.jobs_successful += 1
                except Exception as e:
                    logger.exception("Job processing failed")
                    self._stats.jobs_failed += 1
                    self._emit("error", f"Job failed: {str(e)}")
                
                self._stats.jobs_processed += 1
                self._emit_stats()
            
            # Complete
            self._emit_state(ApplicationState.COMPLETED)
            
        except Exception as e:
            logger.exception("Run loop error")
            self._emit_state(ApplicationState.ERROR)
            self._emit("error", str(e))
        
        finally:
            self._stats.total_runtime_seconds = time.time() - start_time
            self._emit_log(f"⏱ Total runtime: {self._stats.total_runtime_seconds:.1f}s")
            self._emit_stats()
    
    async def _fetch_jobs(self) -> List[Dict]:
        """Fetch jobs from Hunter or return mock data for testing."""
        try:
            # Try to load from existing CSV
            jobs_path = Path("data/jobs.csv")
            if jobs_path.exists():
                import pandas as pd
                df = pd.read_csv(jobs_path)
                jobs = df.to_dict('records')
                self._emit_log(f"Loaded {len(jobs)} jobs from {jobs_path}")
                return jobs[:10]  # Limit for testing
            else:
                self._emit_log("No jobs.csv found, running Hunter...")
                # Run hunter (blocking, but wrapped in executor for async)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._hunter.hunt)
                
                # Reload
                if jobs_path.exists():
                    import pandas as pd
                    df = pd.read_csv(jobs_path)
                    return df.to_dict('records')[:10]
                
                return []
                
        except Exception as e:
            logger.error("Failed to fetch jobs: %s", str(e))
            return []
    
    async def _process_job(self, job_data: Dict) -> None:
        """
        Process a single job application.
        
        This is the core flow:
        1. Navigate to job URL
        2. Scan for form fields
        3. For each field, get answer from Brain
        4. If low confidence, request human input
        5. Fill the form
        6. Submit (unless dry_run)
        """
        # Create job tracking object
        self._current_job = JobApplication(
            job_id=job_data.get("id", "unknown"),
            company=job_data.get("company", "Unknown Company"),
            title=job_data.get("title", "Unknown Title"),
            url=job_data.get("job_url", ""),
            ats_provider=job_data.get("ats_provider", "unknown"),
            started_at=datetime.now()
        )
        
        self._emit_log(f"📄 Processing: {self._current_job.title} @ {self._current_job.company}")
        
        # Step 1: Navigate
        self._emit_state(ApplicationState.NAVIGATING)
        success = await self._vision.navigate(self._current_job.url)
        
        if not success:
            raise Exception(f"Failed to navigate to {self._current_job.url}")
        
        await asyncio.sleep(1)  # Wait for page to stabilize
        
        # Step 2: Scan for fields
        self._emit_state(ApplicationState.SCANNING)
        fields = await self._vision.scan_page()
        self._current_job.fields_detected = len(fields)
        
        if not fields:
            self._emit_log("⚠ No form fields detected on page")
            self._current_job.status = "no_fields"
            return
        
        self._emit_log(f"🔍 Detected {len(fields)} form fields")
        
        # Step 3: Answer questions and fill
        field_answers = {}
        
        for field in fields:
            if self._stop_requested:
                break
            
            # Skip buttons, hidden fields, etc.
            if field.get("type") in ("button", "submit", "hidden"):
                continue
            
            # Get field info
            field_label = field.get("label", "") or field.get("name", "") or field.get("placeholder", "")
            field_selector = field.get("selector", "")
            
            if not field_label:
                continue  # Can't ask Brain without a question
            
            # Step 3a: Ask Brain
            self._emit_state(ApplicationState.ANSWERING)
            self._current_job.questions_asked += 1
            
            answer, confidence = await self._ask_brain(field_label)
            
            # Step 3b: Check confidence threshold
            if confidence < self.CONFIDENCE_THRESHOLD:
                # HUMAN-IN-THE-LOOP: Pause and wait for input
                self._emit_log(f"⚠ Low confidence ({confidence:.2f}) for: {field_label}")
                
                answer = await self._request_human_input(
                    question=field_label,
                    context=f"Field type: {field.get('type')}, Required: {field.get('required')}",
                    field_info=field,
                    brain_suggestion=answer
                )
                
                self._current_job.questions_manual += 1
            
            if answer:
                field_answers[field_selector] = answer
                self._stats.questions_answered += 1
        
        # Step 4: Fill the form
        if field_answers:
            self._emit_state(ApplicationState.FILLING)
            self._emit_log(f"✍ Filling {len(field_answers)} fields...")
            
            results = await self._vision.fill_form(field_answers)
            self._current_job.fields_filled = sum(1 for v in results.values() if v)
        
        # Step 5: Submit (if not dry run)
        if not self.dry_run:
            self._emit_state(ApplicationState.SUBMITTING)
            self._emit_log("📤 Submitting application...")
            
            # Look for submit button
            try:
                await self._vision.click_button(text="Submit")
                await asyncio.sleep(2)  # Wait for submission
                await self._vision.capture_state()  # Capture result
            except Exception as e:
                logger.warning("Submit button click failed: %s", str(e))
        else:
            self._emit_log("🔸 Dry run mode - skipping submission")
        
        # Mark complete
        self._current_job.status = "completed"
        self._current_job.completed_at = datetime.now()
        self._emit_log(f"✓ Completed: {self._current_job.title}")
    
    async def _ask_brain(self, question: str) -> tuple[str, float]:
        """
        Ask the Brain module for an answer.
        
        Returns:
            Tuple of (answer, confidence)
        """
        try:
            response = self._brain.ask_brain(question)
            return response.answer, response.confidence
        except Exception as e:
            logger.error("Brain query failed: %s", str(e))
            return "", 0.0
    
    async def _request_human_input(
        self,
        question: str,
        context: str,
        field_info: Dict,
        brain_suggestion: str
    ) -> str:
        """
        Request human input and wait for response.
        
        This is the PAUSE point in the human-in-the-loop flow.
        
        How it works:
        1. Clear the event (reset to unset)
        2. Emit request_input to frontend
        3. Change state to WAITING_INPUT
        4. await event.wait() - BLOCKS until event.set() is called
        5. Read _pending_input and return
        """
        # Reset the event
        self._human_input_event.clear()
        self._pending_input = None
        
        # Emit request to frontend
        self._emit_state(ApplicationState.WAITING_INPUT)
        self._emit_request_input(
            question=question,
            context=f"{context}\n\nSuggested answer: {brain_suggestion}" if brain_suggestion else context,
            field_info=field_info
        )
        
        self._emit_log(f"⏸ Waiting for human input: {question}")
        
        # BLOCK HERE until submit_override is called
        await self._human_input_event.wait()
        
        # Check if we were stopped instead of getting input
        if self._stop_requested:
            return brain_suggestion or ""
        
        # Return the provided input
        return self._pending_input or brain_suggestion or ""
    
    # =========================================================================
    # STATUS METHODS
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status for API response."""
        return {
            "state": self._state.value,
            "is_running": self._is_running,
            "is_waiting_input": self.is_waiting_input,
            "pending_question": self._pending_question if self.is_waiting_input else None,
            "stats": {
                "jobs_processed": self._stats.jobs_processed,
                "jobs_successful": self._stats.jobs_successful,
                "jobs_failed": self._stats.jobs_failed,
                "questions_answered": self._stats.questions_answered,
                "questions_manual": self._stats.questions_manual_override,
                "runtime_seconds": self._stats.total_runtime_seconds
            },
            "current_job": {
                "id": self._current_job.job_id,
                "company": self._current_job.company,
                "title": self._current_job.title,
                "url": self._current_job.url,
                "status": self._current_job.status,
                "fields_detected": self._current_job.fields_detected,
                "fields_filled": self._current_job.fields_filled
            } if self._current_job else None
        }


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def _test_orchestrator():
    """Quick test of orchestrator initialization."""
    print("=" * 60)
    print("JobOrchestrator Quick Test")
    print("=" * 60)
    
    def on_event(event_type: str, data: Any):
        print(f"[{event_type.upper()}] {json.dumps(data) if isinstance(data, dict) else data}")
    
    orchestrator = JobOrchestrator(
        on_event=on_event,
        headless=False,
        dry_run=True  # Don't actually submit
    )
    
    print(f"\nInitial state: {orchestrator.state}")
    print(f"Is running: {orchestrator.is_running}")
    
    # Note: Full test requires Hunter, Brain, Vision to be working
    print("\n✓ Orchestrator created successfully")
    print("Run 'python server/api.py' to test the full API")


if __name__ == "__main__":
    asyncio.run(_test_orchestrator())
