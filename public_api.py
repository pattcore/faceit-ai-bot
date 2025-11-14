#!/usr/bin/env python3
"""
Public API endpoints for testing
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Public Faceit API")


class PlayerRequest(BaseModel):
    nickname: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_player(request: PlayerRequest):
    """Simple player analysis"""
    try:
        # Mock analysis for now
        return {
            "nickname": request.nickname,
            "analysis": f"Player {request.nickname} analysis complete",
            "kd_ratio": 1.25,
            "win_rate": 65.5,
            "strengths": ["aim", "positioning"],
            "weaknesses": ["consistency"],
            "recommendations": ["Practice daily", "Watch demos"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
