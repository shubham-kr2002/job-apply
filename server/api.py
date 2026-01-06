"""
AI Auto-Applier Agent - Phase 4: FastAPI Server

Real-time API server with WebSocket support for the job application agent.

Features:
- RESTful endpoints for control (start/stop/status)
- WebSocket for real-time updates (logs, screenshots, input requests)
- Human-in-the-loop input submission
- CORS support for Next.js frontend

Endpoints:
- GET  /           - Health check
- GET  /status     - Current orchestrator status
- POST /start      - Start the job application process
- POST /stop       - Gracefully stop the agent
- POST /submit     - Submit human input for pending questions
- WS   /ws         - WebSocket for real-time updates

WebSocket Event Types:
- log:           {"type": "log", "data": "message"}
- state:         {"type": "state", "data": {"state": "...", "timestamp": "..."}}
- screenshot:    {"type": "screenshot", "data": "base64..."}
- request_input: {"type": "request_input", "data": {"question": "...", "context": "..."}}
- stats:         {"type": "stats", "data": {...}}
- error:         {"type": "error", "data": "error message"}
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .orchestrator import JobOrchestrator, ApplicationState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS (Request/Response)
# =============================================================================

class StartRequest(BaseModel):
    """Request body for starting the orchestrator."""
    headless: bool = False
    dry_run: bool = True  # Default to dry run for safety


class SubmitInputRequest(BaseModel):
    """Request body for submitting human input."""
    answer: str


class StatusResponse(BaseModel):
    """Response for status endpoint."""
    state: str
    is_running: bool
    is_waiting_input: bool
    pending_question: Optional[str] = None
    stats: Dict[str, Any]
    current_job: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Generic message response."""
    success: bool
    message: str


# =============================================================================
# WEBSOCKET CONNECTION MANAGER
# =============================================================================

class WebSocketManager:
    """
    Manages WebSocket connections for broadcasting events.
    
    Supports multiple concurrent connections (multiple browser tabs).
    Thread-safe event broadcasting.
    """
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info("WebSocket connected (total: %d)", len(self.active_connections))
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected (total: %d)", len(self.active_connections))
    
    async def broadcast(self, event_type: str, data: Any) -> None:
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event (log, screenshot, request_input, etc.)
            data: Event payload
        """
        message = json.dumps({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connections (handle disconnects gracefully)
        disconnected = []
        
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning("Failed to send to WebSocket: %s", str(e))
                    disconnected.append(connection)
        
        # Remove disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    def broadcast_sync(self, event_type: str, data: Any) -> None:
        """
        Synchronous broadcast wrapper for use in non-async contexts.
        
        Creates a new task to handle the broadcast.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(event_type, data))
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except RuntimeError:
            # No event loop, log and skip
            logger.warning("Cannot broadcast, no event loop available")
    
    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self.active_connections)


# =============================================================================
# GLOBAL STATE
# =============================================================================

# WebSocket manager (singleton)
ws_manager = WebSocketManager()

# Orchestrator instance (singleton, created on demand)
_orchestrator: Optional[JobOrchestrator] = None


def get_orchestrator() -> JobOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = JobOrchestrator(
            on_event=ws_manager.broadcast_sync,
            headless=False,
            dry_run=True
        )
    return _orchestrator


# =============================================================================
# FASTAPI APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 AI Auto-Applier API Server starting...")
    logger.info("WebSocket endpoint: ws://localhost:8000/ws")
    logger.info("API docs: http://localhost:8000/docs")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    orchestrator = get_orchestrator()
    if orchestrator.is_running:
        await orchestrator.stop()
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Auto-Applier Agent API",
    description="Real-time job application automation with human-in-the-loop support",
    version="0.4.0",
    lifespan=lifespan
)

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"  # Allow all for development (restrict in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@app.get("/", response_model=MessageResponse)
async def health_check():
    """Health check endpoint."""
    return MessageResponse(
        success=True,
        message="AI Auto-Applier Agent API is running"
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Get current orchestrator status.
    
    Returns state, statistics, and current job info.
    """
    orchestrator = get_orchestrator()
    status = orchestrator.get_status()
    
    return StatusResponse(
        state=status["state"],
        is_running=status["is_running"],
        is_waiting_input=status["is_waiting_input"],
        pending_question=status.get("pending_question"),
        stats=status["stats"],
        current_job=status.get("current_job")
    )


@app.post("/start", response_model=MessageResponse)
async def start_agent(request: StartRequest):
    """
    Start the job application process.
    
    Launches the orchestrator in a background task.
    Non-blocking - returns immediately.
    """
    global _orchestrator
    
    orchestrator = get_orchestrator()
    
    if orchestrator.is_running:
        raise HTTPException(
            status_code=409,
            detail="Agent is already running. Stop it first with POST /stop"
        )
    
    # Recreate orchestrator with new settings
    _orchestrator = JobOrchestrator(
        on_event=ws_manager.broadcast_sync,
        headless=request.headless,
        dry_run=request.dry_run
    )
    
    # Start in background
    await _orchestrator.start()
    
    return MessageResponse(
        success=True,
        message=f"Agent started (headless={request.headless}, dry_run={request.dry_run})"
    )


@app.post("/stop", response_model=MessageResponse)
async def stop_agent():
    """
    Gracefully stop the agent.
    
    Finishes current job and cleans up resources.
    """
    orchestrator = get_orchestrator()
    
    if not orchestrator.is_running:
        return MessageResponse(
            success=True,
            message="Agent is not running"
        )
    
    await orchestrator.stop()
    
    return MessageResponse(
        success=True,
        message="Agent stopped successfully"
    )


@app.post("/submit", response_model=MessageResponse)
async def submit_override(request: SubmitInputRequest):
    """
    Submit human input to resolve a pending question.
    
    Called when the agent is in WAITING_INPUT state.
    Wakes up the paused orchestrator coroutine.
    """
    orchestrator = get_orchestrator()
    
    if not orchestrator.is_waiting_input:
        raise HTTPException(
            status_code=400,
            detail="Agent is not waiting for input"
        )
    
    success = await orchestrator.submit_override(request.answer)
    
    if success:
        return MessageResponse(
            success=True,
            message="Input submitted successfully"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit input"
        )


@app.get("/jobs")
async def get_jobs():
    """
    Get list of discovered jobs from CSV.
    
    Returns the jobs that have been scraped by Hunter.
    """
    from pathlib import Path
    
    jobs_path = Path("data/jobs.csv")
    if not jobs_path.exists():
        return {"jobs": [], "count": 0}
    
    try:
        import pandas as pd
        df = pd.read_csv(jobs_path)
        jobs = df.to_dict('records')
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    Clients connect here to receive:
    - Log messages
    - Screenshots (base64)
    - State changes
    - Input requests (human-in-the-loop)
    - Statistics updates
    
    The connection stays open and receives events as they occur.
    """
    await ws_manager.connect(websocket)
    
    # Send initial status on connect
    orchestrator = get_orchestrator()
    await websocket.send_json({
        "type": "connected",
        "data": {
            "message": "Connected to AI Auto-Applier Agent",
            "status": orchestrator.get_status()
        },
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30  # Heartbeat interval
                )
                
                # Parse and handle client messages
                try:
                    message = json.loads(data)
                    msg_type = message.get("type", "")
                    
                    if msg_type == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    elif msg_type == "submit_input":
                        # Allow input submission via WebSocket too
                        answer = message.get("answer", "")
                        if answer and orchestrator.is_waiting_input:
                            await orchestrator.submit_override(answer)
                    
                    elif msg_type == "get_status":
                        await websocket.send_json({
                            "type": "status",
                            "data": orchestrator.get_status(),
                            "timestamp": datetime.now().isoformat()
                        })
                    
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received: %s", data[:100])
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception:
                    break  # Connection lost
                    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
    finally:
        await ws_manager.disconnect(websocket)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server with uvicorn."""
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("AI Auto-Applier Agent - Phase 4: API Server")
    logger.info("=" * 60)
    logger.info(f"Starting server at http://{host}:{port}")
    logger.info(f"API Documentation: http://{host}:{port}/docs")
    logger.info(f"WebSocket: ws://{host}:{port}/ws")
    logger.info("=" * 60)
    
    uvicorn.run(
        "server.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)
