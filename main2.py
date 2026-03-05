from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import httpx    #비동기 통신을 위해 추천

app = FastAPI()

# 1. CORS 설정 (브라우저 테스트 필수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 데이터 모델 정의
class AgentStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    message: str
    result: Optional[dict] = None

@app.get("/")
async def get_dashboard():
    # index.html 파일이 main.py와 같은 폴더에 있어야 합니다.
    return FileResponse("index.html")

# 3. 일반 API (Swagger에 "GET"으로 표시됨)
@app.get("/status/{task_id}", response_model=AgentStatus)
async def get_task_status(task_id: str):
    return {
        "task_id": task_id,
        "status": "analyzing",
        "progress": 70,
        "message": "데이터 분석 단계에 진입했습니다.",
        "result": None
    }

# 4. 실시간 WebSocket (Swagger에는 기본적으로 표시되지 않음)
@app.websocket("/ws/status/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    # 0%부터 100%까지 시뮬레이션
    for i in range(0, 101, 10):
        await asyncio.sleep(1)
        data = AgentStatus(
            task_id=task_id,
            status="processing",
            progress=i,
            message=f"현재 {i}% 진행 중..."
        )
        await websocket.send_json(data.model_dump())
    await websocket.close()
    
@app.post("/ask")
async def ask_ai(prompt: str, model: str = "llama3"):
    url = "http://localhost:11434/api/generate" # Ollama 기본 서버 주소
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": 1000,
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=60.0)
        result = response.json()
        return {"answer": result['response']}