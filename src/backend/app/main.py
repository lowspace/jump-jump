# /src/backend/app/main.py
# FastAPI main application for Jump Jump

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Optional
from pathlib import Path

from ..core.config import server_config
from .game_engine import game_engine
from .ws_handler import ws_manager
from .state_manager import state_manager
from .insight_system import insight_system


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting Jump Jump server...")
    print(f"CORS origins: {server_config.CORS_ORIGINS}")
    yield
    # Shutdown
    print("Shutting down Jump Jump server...")


# Create FastAPI app
app = FastAPI(
    title="Jump Jump API",
    description="Web-based narrative adventure game API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


# ==================== REST API Routes ====================

@app.get("/")
async def root():
    """Serve the frontend game page"""
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "name": "Jump Jump API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "game_start": "/api/game/start",
            "game_state": "/api/game/{session_id}/state",
            "game_action": "/api/game/{session_id}/action",
            "insight": "/api/game/{session_id}/insight",
            "websocket": "/ws/{session_id}",
            "frontend": "/static/index.html"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/game/start")
async def start_game(
    resume_session_id: Optional[str] = None,
    start_scene: str = "scene-0-wuzhishan",
    player_role: str = "少年樵夫"
):
    """
    Start a new game or resume an existing session

    Args:
        resume_session_id: Optional session ID to resume
        start_scene: Scene to start from (default: scene-0-wuzhishan)
        player_role: Player role name

    Returns:
        Game start response with session_id and initial state
    """
    if resume_session_id:
        # Resume existing session
        state = state_manager.load_session(resume_session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": resume_session_id,
            "current_scene": state["current_scene"],
            "current_phase": state["current_phase"],
            "narrative_text": "继续游戏...",
            "available_actions": [],  # Will be populated by game engine
            "insight_quota": insight_system.get_quota_status(state),
            "player_state": {
                "role": state["player_role"],
                "faith_erosion_level": state["faith_erosion_level"]
            },
            "resumed": True
        }

    # Create new session
    result = await game_engine.create_session(start_scene, player_role)
    return result


@app.get("/api/game/{session_id}/state")
async def get_game_state(session_id: str):
    """
    Get current game state

    Args:
        session_id: Game session ID

    Returns:
        Current game state
    """
    state = await game_engine.get_game_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@app.post("/api/game/{session_id}/action")
async def submit_action(session_id: str, action: dict):
    """
    Submit a player action

    Args:
        session_id: Game session ID
        action: Action details
            {
                "action_type": "dialogue|decision|move|observe",
                "target": "string|null",
                "content": "string"
            }

    Returns:
        Action result with narrative and updates
    """
    result = await game_engine.process_action(session_id, action)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/api/game/{session_id}/insight")
async def use_insight(session_id: str, insight_request: dict):
    """
    Use insight

    Args:
        session_id: Game session ID
        insight_request: Insight usage details
            {
                "insight_type": "true_purpose|behind_dialogue",
                "target": "string"
            }

    Returns:
        Insight reveal result
    """
    result = await game_engine.use_insight(
        session_id,
        insight_request.get("insight_type"),
        insight_request.get("target")
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@app.get("/api/game/{session_id}/checkpoints")
async def get_checkpoints(session_id: str):
    """
    Get session checkpoints

    Args:
        session_id: Game session ID

    Returns:
        List of checkpoints
    """
    checkpoints = state_manager.get_session_checkpoints(session_id)
    return {"checkpoints": checkpoints}


@app.post("/api/game/{session_id}/checkpoint/{checkpoint_id}/load")
async def load_checkpoint(session_id: str, checkpoint_id: str):
    """
    Load a checkpoint

    Args:
        session_id: Game session ID
        checkpoint_id: Checkpoint ID to load

    Returns:
        Loaded game state
    """
    state = state_manager.load_checkpoint(checkpoint_id)
    if not state:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    if state.get("session_id") != session_id:
        raise HTTPException(status_code=403, detail="Checkpoint does not belong to session")

    return {
        "session_id": session_id,
        "checkpoint_loaded": True,
        "turn_count": state["turn_count"],
        "current_scene": state["current_scene"]
    }


@app.post("/api/game/{session_id}/transition")
async def transition_scene(session_id: str, transition: dict = None):
    """
    Transition to a new scene

    Args:
        session_id: Game session ID
        transition: Optional transition details
            {
                "new_scene": "scene-id"  # If not provided, auto-determine next scene
            }

    Returns:
        Transition result
    """
    transition = transition or {}
    new_scene = transition.get("new_scene")

    # If no new_scene provided, auto-determine next scene
    if not new_scene:
        state = state_manager.load_session(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")

        current_scene = state["current_scene"]
        from ..core.config import SCENE_ORDER

        try:
            current_idx = SCENE_ORDER.index(current_scene)
            if current_idx < len(SCENE_ORDER) - 1:
                new_scene = SCENE_ORDER[current_idx + 1]
            else:
                # Already at last scene
                return {
                    "session_id": session_id,
                    "current_scene": current_scene,
                    "message": "已经到达最后一个场景",
                    "game_complete": True
                }
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown current scene: {current_scene}")

    result = await game_engine.transition_to_scene(session_id, new_scene)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ==================== WebSocket Route ====================

@app.websocket("/ws/{session_id}")
async def game_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time game communication

    Message format (client -> server):
    {
        "type": "action|insight|ping|get_state|transition_scene",
        "payload": {...}
    }

    Message format (server -> client):
    {
        "type": "narrative|reveal|decision_prompt|scene_transition|error|ack",
        "payload": {...}
    }
    """
    await ws_manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Handle message
            response = await ws_manager.handle_message(
                session_id, data, game_engine
            )

            # Send response
            await websocket.send_json(response)

    except WebSocketDisconnect:
        await ws_manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error for {session_id}: {e}")
        await ws_manager.disconnect(session_id)


# ==================== Admin/Debug Routes ====================

@app.get("/api/admin/sessions")
async def list_sessions(limit: int = 10):
    """List recent game sessions (admin only)"""
    sessions = state_manager.list_sessions(limit)
    return {"sessions": sessions}


@app.delete("/api/admin/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a game session (admin only)"""
    success = state_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    return {"deleted": True, "session_id": session_id}


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=server_config.HOST,
        port=server_config.PORT,
        reload=server_config.DEBUG
    )
